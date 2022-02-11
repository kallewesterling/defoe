""" 
Identify the locations per page and geo-resolve them. 
It uses the Original Edinburgh geoparser pipeline for identifying all the posible locations within a page and georesolve them.
"""

from defoe import query_utils
from defoe.nls.query_utils import clean_page_as_string
from pyspark.sql import Row, SparkSession, SQLContext

import yaml, os


def do_query(archives, config_file=None, logger=None, context=None):
    """
    It ingests NLS pages, applies the original geoparser for identifying the possible locations of each page. 
    And also for getting the latituted and longitude of each location.
    
    Before applying the geoparser, two clean steps are applied - long-S and hyphen words. 
    
    A config_file should be indicated to specify the gazetteer to use, 
    the defoe_path, the bounding box (optional), as well as the operating system. 
    
    Example:
    - 1842:
        - archive: /home/rosa_filgueira_vicente/datasets/sg_simple_sample/97437554
        - edition: 1842, Volume 1
        - georesolution_page:
            - Annan-rb17:
              - in-cc: ''
              - lat: '54.98656134974328'
              - long: '-3.259540348679'
              - pop: ''
              - snippet: is 8 miles north-west of Annan , and commands a fine
              - type: ppl
            - Annan-rb18:
              - in-cc: ''
              - lat: '54.98656134974328'
              - long: '-3.259540348679'
              - pop: ''
              - snippet: valley is washed by the Annan , and lies open from
              - type: ppl
            ....   
        - lang_model: geoparser_original
        - page_filename: alto/97440572.34.xml
        - text_unit id: Page252
        - title: topographical, statistical, and historical gazetteer of Scotland

    :param archives: RDD of defoe.nls.archive.Archive
    :type archives: pyspark.rdd.PipelinedRDD
    :param config_file: query configuration file
    :type config_file: str or unicode
    :param logger: logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: "0"
    :rtype: string
    """
    with open(config_file, "r") as f:
        config = yaml.load(f)
    gazetteer = config["gazetteer"]
    if "bounding_box" in config:
        bounding_box = " -lb " + config["bounding_box"] + " 2"
    else:
        bounding_box = ""
    if "os_type" in config:
        if config["os_type"] == "linux":
            os_type = "sys-i386-64"
        else:
            os_type = "sys-i386-snow-leopard"
    else:
        os_type = "sys-i386-64"
    if "defoe_path" in config:
        defoe_path = config["defoe_path"]
    else:
        defoe_path = "./"

    documents = archives.flatMap(
        lambda archive: [
            (
                document.year,
                document.title,
                document.edition,
                document.archive.filename,
                document,
            )
            for document in list(archive)
        ]
    )

    # [(tittle, edition, year, archive name, page filename, text_unit, text_unit_id,
    #   num_text_unit, type of archive, type of disribution, model, clean_page)]

    pages_clean = documents.flatMap(
        lambda year_document: [
            (
                year_document[0],
                year_document[1],
                year_document[2],
                year_document[3],
                page.code,
                page.page_id,
                clean_page_as_string(page, defoe_path, os_type),
            )
            for page in year_document[4]
        ]
    )

    geo_xml_pages = pages_clean.flatMap(
        lambda clean_page: [
            (
                clean_page[0],
                clean_page[1],
                clean_page[2],
                clean_page[3],
                clean_page[4],
                clean_page[5],
                query_utils.geoparser_cmd(
                    clean_page[6], defoe_path, os_type, gazetteer, bounding_box
                ),
            )
        ]
    )

    matching_pages = geo_xml_pages.map(
        lambda geo_page: (
            geo_page[0],
            {
                "title": geo_page[1],
                "edition": geo_page[2],
                "archive": geo_page[3],
                "page_filename": geo_page[4],
                "text_unit id": geo_page[5],
                "lang_model": "geoparser_original",
                "georesolution_page": query_utils.geoparser_coord_xml(geo_page[6]),
            },
        )
    )

    result = (
        matching_pages.groupByKey()
        .map(lambda date_context: (date_context[0], list(date_context[1])))
        .collect()
    )

    return result
