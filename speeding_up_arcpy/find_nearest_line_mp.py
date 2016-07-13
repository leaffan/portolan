#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""
Parallel version of a script to retrieve nearest line features to set of point features.
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


def find_nearest_line(func_data):
    # unpacking provided function data
    point_lyr_src, line_lyr_src, oid_lower_bound, oid_upper_bound = func_data
    
    # creating ESRI feature layers
    point_lyr = arcpy.management.MakeFeatureLayer(point_lyr_src, "point_layer")
    line_lyr = arcpy.management.MakeFeatureLayer(line_lyr_src, "line_layer")

    # retrieving OID and shape field names for point feature layer
    oid_fieldname = arcpy.Describe(point_lyr).OIDFieldName
    shape_fieldname = arcpy.Describe(point_lyr).shapeFieldName

    # setting up where clause to restrict selection to specified oid range
    where_clause = "%s >= %d AND %s <= %d" % (oid_fieldname, oid_lower_bound, oid_fieldname, oid_upper_bound)
    # re-creating point feature layer
    arcpy.management.Delete(point_lyr)
    point_lyr = arcpy.management.MakeFeatureLayer(point_lyr_src, "point_layer", where_clause)

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

def chunks(l, n):
    u"""
    Yields successive n-sized chunks from l with the last chunk containing
    m (< n) elements.
    """
    for i in xrange(0, len(l), n):
        yield l[i : i + n]

def get_equal_parts(lyr, size):
    u"""
    Creates oid ranges with given maximum size from specified layer.
    """
    print "Creating oid ranges with maximum size %d" % size
    
    all_oids = list()
    
    with arcpy.da.SearchCursor(lyr, ["OID@"]) as cursor:
        for oid, in cursor:
            all_oids.append(oid)
    
    print "%d oids found overall" % len(all_oids)
    equal_parts = list(chunks(sorted(all_oids), size))
    print "%d oid ranges created" % len(equal_parts)
    return equal_parts

if __name__ == '__main__':
    equal_parts = get_equal_parts(point_lyr_src, 20)   

    mp_func_data = list()
    i = 0
    for eq in equal_parts:
        i += 1
        print "part %2d - lower oid bound: %4d - upper oid bound: %4d - size: %2d" % (i, eq[0], eq[-1], len(eq))
        mp_func_data.append([point_lyr_src, line_lyr_src, eq[0], eq[-1]])
        
    # setting up pool of four workers
    pool = multiprocessing.Pool(4, None, None, 1)
    # setting up list for all results
    all_results = list()

    # mapping function for nearest line retrieval (with input data) to worker pool
    for worker_results in pool.map(find_nearest_line, mp_func_data):
        all_results.extend(worker_results)

    # closing pool and waiting for each task to be finished
    pool.close()
    pool.join()
    