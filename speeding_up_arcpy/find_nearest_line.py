#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""
Linear version of a script to retrieve nearest line features to set of point features.
"""

import os, sys
import arcpy

sde_connection_file = "sde_connection.sde"

point_src_dataset = "FDS_POINT"
point_src_featureclass = "FCL_POINT"

line_src_dataset = "FDS_LINE"
line_src_featureclass = "FCL_LINE"

buffer_base_increment = 10

point_lyr_src = '\\'.join((sde_connection_file, point_src_dataset, point_src_featureclass))
line_lyr_src = '\\'.join((sde_connection_file, line_src_dataset, line_src_featureclass))


def find_nearest_line(point_lyr_src, line_lyr_src):
    # creating ESRI feature layers
    point_lyr = arcpy.management.MakeFeatureLayer(point_lyr_src, "point_layer")
    line_lyr = arcpy.management.MakeFeatureLayer(line_lyr_src, "line_layer")

    # retrieving OID and shape field names for point feature layer
    oid_fieldname = arcpy.Describe(point_lyr).OIDFieldName
    shape_fieldname = arcpy.Describe(point_lyr).shapeFieldName

    # setting up container for resulting pairs of points and least-distance lines
    pnt_min_dist_line_pairs = list()
    
    with arcpy.da.SearchCursor(point_lyr, ["OID@", "SHAPE@"]) as point_cursor:
        for poid, geom in point_cursor:
            print "Working on point feature %d" % poid
            # setting up a where clause to create a feature layer that solely contains the current point of interest
            poi_where_clause = "%s = %d" % (oid_fieldname, poid)
            # crreating that feature layer that will be used as foundation for distance calculation
            poi_lyr = arcpy.management.MakeFeatureLayer(point_lyr, "poi_layer", poi_where_clause)
    
            buffer_radius = 0
            nearby_lines_cnt = 0
            i = 1
            
            while not nearby_lines_cnt:
                # setting initial buffer radius to base size or incrementing
                # current buffer radius by base size (non-linear)
                buffer_radius += i * buffer_base_increment
                # finding all line elements that are within a distance of
                # buffer radius from the point of interest
                nearby_lines_lyr = arcpy.management.SelectLayerByLocation(line_lyr, "WITHIN_A_DISTANCE", poi_lyr, buffer_radius)
                nearby_lines_cnt = int(arcpy.management.GetCount(nearby_lines_lyr).getOutput(0))
                i += 1

            print "Number of line features found within %d m of point feature %d: %d" % (buffer_radius, poid, nearby_lines_cnt)
            
            # retrieving point geometry
            point_geom = arcpy.PointGeometry(geom.getPart())
    
            # setting up minimal distance variables
            minimal_distance = sys.maxsize
            minimal_distance_line_oid = None
    
            # from all found lines within buffer radius find the one with the
            # smallest distance to the point of interest feature
            with arcpy.da.SearchCursor(nearby_lines_lyr, ["OID@", "SHAPE@"]) as line_cursor:
                for loid, lgeom in line_cursor:
                    line_geom = arcpy.Polyline(lgeom.getPart())
                    distance = point_geom.distanceTo(line_geom)
    
                    if distance < minimal_distance:
                        minimal_distance = distance
                        minimal_distance_line_oid = loid

            print "Minimum distance calculated between point feature %d and line feature %d: %0.2f" % (poid, minimal_distance_line_oid, minimal_distance)
            
            arcpy.management.Delete(poi_lyr)

            pnt_min_dist_line_pairs.append((poid, minimal_distance_line_oid, minimal_distance))
                        
            print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

    return pnt_min_dist_line_pairs

if __name__ == '__main__':
    
    point_with_least_distance_lines = find_nearest_line(point_lyr_src, line_lyr_src)