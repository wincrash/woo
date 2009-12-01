
def getRealVersion():
	"Attempts to get yade version from RELEASE file if it exists or from bzr or svn."
	import os.path,re,os
	if os.path.exists('RELEASE'):
		return file('RELEASE').readline().strip()
	if os.path.exists('.svn'):
		for l in os.popen("LC_ALL=C svn info").readlines():
			m=re.match(r'Revision: ([0-9]+)',l)
			if m: return 'svn'+m.group(1)
	if os.path.exists('.bzr'):
		for l in os.popen("LC_ALL=C bzr version-info 2>/dev/null").readlines():
			m=re.match(r'revno: ([0-9]+)',l)
			if m: return 'bzr'+m.group(1)
	return None


class Plugin:
	def __init__(self,name,src,deps,feats,module):
		self.name,self.src,self.deps,self.feats,self.module=name,src,deps,feats,module
	def __str__(self):
		return '%s/%s [%s] (%s)'%(self.module,self.name,','.join(self.feats),','.join(self.libs))

def grepForIncludes(root,f):
	import re
	ret=set()
	skipping=False
	lineNo=0
	for l in open(root+'/'+f):
		if re.match(r'\s*#endif.*$',l): skipping=False; continue
		if skipping: continue
		m=re.match(r'^\s*#include\s*<yade/([^/]*)/(.*)>.*$',l)
		if m:
			incMod=m.group(1); baseName=m.group(2).split('.')[0];
			if incMod=='core' or incMod.startswith('lib-'): continue
			if skipping: continue
			ret.add(baseName)
			continue
		m=re.match(r'\s*#ifdef\s*YADE_(.*)\s*$',l)
		if m:
			feat=m.group(1).lower()
			if feat not in features: skipping=True; continue
	return ret

features=[]

def scanAllPlugins(cacheFile,feats):
	"""Traverse all files in pkg/, recording what plugins they link with and what features they require.
	Save the result in a cache file and only regenerate the information if the cache file is missing."""
	import os, os.path, re, shelve
	features=feats # update the module-level var
	if cacheFile:
		refresh=os.path.exists(cacheFile)
		plugInfo=shelve.open(cacheFile)
	else:
		plugInfo={}; refresh=True
	if refresh:
		for root, dirs, files in os.walk('pkg/',topdown=True):
			for f in files:
				if not (f.endswith('.cpp') or f.endswith('.cc') or f.endswith('C')): continue
				ff=root+'/'+f
				linkDeps,featureDeps=set(),set()
				isPlugin=True #False
				skipping=False
				for l in open(ff):
					if re.match(r'\s*#endif.*$',l): skipping=False; continue
					if skipping: continue
					m=re.match(r'\s*#ifdef\s*YADE_(.*)\s*$',l)
					if m:
						feat=m.group(1).lower()
						if feat not in features: skipping=True
					if re.match(r'\s*YADE_PLUGIN\(.*',l): isPlugin=True
					m=re.match(r'^\s*#include\s*<yade/([^/]*)/(.*)>.*$',l)
					if m:
						incMod=m.group(1); incHead=m.group(2); baseName=incHead.split('.')[0]; assert(len(incHead.split('.'))==2)
						if incMod=='core' or incMod.startswith('lib-'): continue
						if os.path.exists(root+'/'+m.group(2)):
							linkDeps.update(grepForIncludes(root,m.group(2)))
						linkDeps.add(incHead.split('.')[0])
						continue
					m=re.match('^\s*YADE_REQUIRE_FEATURE\((.*)\).*$',l)
					if m:
						featureDeps.add(m.group(1).upper())
					m=re.match('^\s*#include\s*"([^/]*)".*$',l)
					if m:
						inc=m.group(1); incBaseName=m.group(1).split('.')[0]
						if not os.path.exists(root+'/'+m.group(1)):
							print "WARNING: file %s included from %s doesn't exist"%(m.group(1),ff)
						else:
							linkDeps.update(grepForIncludes(root,m.group(1)))
							continue
				if isPlugin:
					plugin=f.split('.')[0]
					m=re.match(r'.*pkg/([^/]*)(/.*|)$',root)
					plugInfo[plugin]=Plugin(plugin,ff,linkDeps,featureDeps,m.group(1))
	pp={}
	for p in plugInfo.keys(): pp[p]=plugInfo[p]
	if cacheFile: plugInfo.close()
	return pp

def getWantedPlugins(plugInfo,excludes,features,linkStrategy):
	"""Use pluginInfo (generated by scanAllPlugins) and return only plugins that we should build,
	based on excludes and available features.
	
	Set the plugin object according to linkStrategy and set also other plugins this one should link to."""
	ret={}
	feats=set([feat.upper() for feat in features])
	excludes=set(excludes)
	for p in plugInfo:
		plug=plugInfo[p]
		if plug.module in excludes: continue
		if not plug.feats<=feats:
			continue # plugin needs more feature than we have
		ret[plug.name]=plug
	for p in plugInfo.values(): p.obj=getPluginObj(p,linkStrategy)
	for p in plugInfo.values(): p.libs=getPluginLibs(p,plugInfo)
	return ret

def getPluginObj(plug,linkStrategy):
	"""Return name of library this plugin will be compiled into, based on current linkStrategy."""
	if   linkStrategy=='per-class': return plug.name
	elif linkStrategy=='per-pkg': return plug.module
	elif linkStrategy=='monolithic': return 'packages'
	elif linkStrategy=='static': return 'packages'

def getPluginLibs(p,plugInfo):
	"""Returns library names this plugin should link to, based on current information about other plugins."""
	ret=set()
	for dep in p.deps:
		if dep in plugInfo.keys():
			ret.add(plugInfo[dep].obj)
		else:
			pass
			#print p.src+':',dep,"not a plugin?"
	ret.discard(p.obj)
	return ret

def buildPluginLibs(env,plugInfo):
	objs={}
	linkStrategy=env['linkStrategy']
	chunkSize=env['chunkSize']
	for p in plugInfo.values():
		if not objs.has_key(p.obj): objs[p.obj]=(set(),set())
		objs[p.obj][0].add(p.src)
		objs[p.obj][1].update(p.libs)
	for obj in objs.keys():
		srcs=list(objs[obj][0])
		if len(srcs)>1:
			if len(srcs)<chunkSize: srcs=env.Combine('$buildDir/'+obj+'.cpp',srcs)
			# thanks to http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python :
			else: srcs=[env.Combine('$buildDir/'+obj+'%d.cpp'%j,srcs[i:i+chunkSize]) for j,i in enumerate(range(0,len(srcs),chunkSize))]
		if linkStrategy!='static':
			env.Install('$PREFIX/lib/yade$SUFFIX/plugins',env.SharedLibrary(obj,srcs,LIBS=env['LIBS']+['yade-support','core']+list(objs[obj][1])))
		else:
			env.Install('$PREFIX/lib/yade$SUFFIX/plugins',env.StaticLibrary(obj,srcs,LIBS=env['LIBS']+['yade-support','core']+list(objs[obj][1])))
	

	




