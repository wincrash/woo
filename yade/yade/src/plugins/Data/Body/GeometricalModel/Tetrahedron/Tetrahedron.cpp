/***************************************************************************
 *   Copyright (C) 2004 by Janek Kozicki                                   *
 *   cosurgi@berlios.de                                                    *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/

///////////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////

#include "Tetrahedron.hpp"

///////////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////

Tetrahedron::Tetrahedron() : GeometricalModel()
{
	createIndex();
}

Tetrahedron::Tetrahedron(Vector3r& p1,Vector3r& p2,Vector3r& p3,Vector3r& p4) : GeometricalModel()
{
	createIndex();
	v1 = p1;
	v2 = p2;
	v3 = p3;
	v4 = p4;
}

Tetrahedron::~Tetrahedron()
{
}

void Tetrahedron::registerAttributes()
{
	GeometricalModel::registerAttributes();
	// FIXME
	REGISTER_ATTRIBUTE(v1); // no need to save them (?)
	REGISTER_ATTRIBUTE(v2); // no need to save them (?)
	REGISTER_ATTRIBUTE(v3); // no need to save them (?)
	REGISTER_ATTRIBUTE(v4); // no need to save them (?)
}
