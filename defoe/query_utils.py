"""
Query-related utility functions and types.
"""

try:
    import spacy
    from spacy.tokens import Doc
    from spacy.vocab import Vocab
except ImportError:
    raise ImportError(
        "SpaCy cannot be loaded. Make sure you have installed it."
    )

try:
    from nltk.stem import PorterStemmer, WordNetLemmatizer
except ImportError:
    raise ImportError(
        "NLTK stemmers and lemmatizers cannot be loaded. Make sure you have installed them."  # noqa
    )

try:
    from elasticsearch import Elasticsearch
except ImportError:
    # print("Warning: Could not import ElasticSearch. Functions related to ES won't work.") # noqa
    pass

from lxml import etree
import enum
import os
import re
import subprocess
import yaml


NON_AZ_REGEXP = re.compile("[^a-z]")
NON_AZ_19_REGEXP = re.compile("[^a-z0-9]")


class PreprocessWordType(enum.Enum):
    """
    Word preprocessing types.
    """

    NORMALIZE = 1  # Normalize word
    STEM = 2  # Normalize and stem word
    LEMMATIZE = 3  # Normalize and lemmatize word
    NONE = 4  # Apply no preprocessing
    NORMALIZE_NUM = 5  # Normalize word including numbers


PREPROCESS_WORD_TYPES = [
    k.lower() for k in list(PreprocessWordType.__members__.keys())
]


def parse_preprocess_word_type(type_str: str) -> PreprocessWordType:
    """
    Parse a string into a ``defoe.query_utils.PreprocessWordType``.

    :param type_str: One of none|normalize|stem|lemmatize
    :type type_str: str
    :return: Word preprocessing type
    :rtype: defoe.query_utils.PreprocessWordType
    :raises ValueError: If "preprocess" is not one of the expected values
    """

    try:
        preprocess_type = PreprocessWordType[type_str.upper()]
    except KeyError:
        raise KeyError(
            f"preprocess must be one of {PREPROCESS_WORD_TYPES} but is '{type_str}'"  # noqa
        )

    return preprocess_type


def extract_preprocess_word_type(
    config: dict, default: PreprocessWordType = PreprocessWordType.LEMMATIZE
) -> PreprocessWordType:
    """
    Extract PreprocessWordType from "preprocess" dictionary value in query
    configuration.

    :param config: Configuration dictionary
    :type config: dict
    :param default: default value if "preprocess" is not found
    :type default: defoe.query_utils.PreprocessWordType
    :return: Word preprocessing type
    :rtype: defoe.query_utils.PreprocessWordType
    :raises: ValueError if "preprocess" is not one of
        none|normalize|stem|lemmatize
    """
    if "preprocess" not in config:
        preprocess_type = default
    else:
        preprocess_type = parse_preprocess_word_type(config["preprocess"])

    return preprocess_type


def extract_data_file(config: dict, default_path: str) -> str:
    """
    Extract data file path from "data" dictionary value in query configuration.

    :param config: Configuration dictionary
    :type config: dict
    :param default_path: Default path to prepend to data file path if data
        file path is a relative path
    :type default_path: str
    :return: File path
    :rtype: str
    :raises KeyError: If "data" is not in config
    """

    if "data" not in config:
        raise KeyError(
            "Configuration file does not contain the required data value with a path to a data file."  # noqa
        )

    data_file = config["data"]

    if not os.path.isabs(data_file):
        data_file = os.path.join(default_path, data_file)

    return data_file


def extract_window_size(config: dict, default=10):
    """
    Extract window size from "window" dictionary value in query configuration.

    :param config: Configuration dictionary
    :type config: dict
    :param default: default value if "window" is not found
    :type default: int
    :return: Window size
    :rtype: int
    :raises: ValueError if "window" is >= 1
    """

    if "window" not in config:
        window = default
    else:
        window = config["window"]

    if window < 1:
        raise ValueError("window must be at least 1")

    return window


def extract_years_filter(config: dict):
    """
    Extract min and max years to filter data from "years_filter" dictionary
    value the query configuration. The years will be split using the "-"
    character.

    years_filter: 1780-1918

    :param config: Configuration dictionary
    :type config: dict
    :return: Min_year, max_year
    :rtype: int, int
    """

    if "years_filter" not in config:
        raise ValueError("years_filter value not found in the config file")

    years = config["years_filter"]
    year_min = years.split("-")[0]
    year_max = years.split("-")[1]

    return year_min, year_max


def extract_output_path(config: dict) -> str:
    """
    Extract output path from "output_path" dictionary value the query
    configuration.

    output_path: /home/users/rfilguei2/LwM/defoe/OUTPUT/

    :param config: Configuration dictionary
    :type config: dict
    :return: A path to an output directory, defaults to ``.``
    :rtype: str
    """

    if "output_path" not in config:
        output_path = "."
    else:
        output_path = config["output_path"]

    return output_path


def extract_fuzzy(config: dict, kind: str = "target") -> bool:
    """
    Extract boolean for fuzzy search dictionary value from the query
    configuration file.

    fuzzy_target: False
    fuzzy_keyword: True

    :param config: Configuration dictionary
    :type config: dict
    :param kind: Kind, defaults to ``target``
    :type kind: str
    :return: Boolean for fuzzy search, defaults to False
    :rtype: bool
    """

    if f"fuzzy_{kind}" not in config:
        return False

    if isinstance(config[f"fuzzy_{kind}"], bool):
        return config[f"fuzzy_{kind}"]

    if (
        config[f"fuzzy_{kind}"].lower() == "true"
        or config[f"fuzzy_{kind}"].lower() == "1"
    ):
        return True

    return False


def normalize(word: str) -> str:
    """
    Normalize a word by converting it to lowercase and removing all
    characters that are not ``a-z`` or ``A-Z``.

    :param word: Word to normalize
    :type word: str
    :return: Normalized word
    :rtype word: str
    """

    return re.sub(NON_AZ_REGEXP, "", word.lower())


def normalize_including_numbers(word: str) -> str:
    """
    Normalize a word by converting it to lowercase and removing all
    characters that are not ``a-z``, ``A-Z`` or ``0-9``.

    :param word: Word to normalize
    :type word: str
    :return: Normalized word
    :rtype word: str
    """

    return re.sub(NON_AZ_19_REGEXP, "", word.lower())


def stem(word: str) -> str:
    """
    Reducing word to its word stem, base or root form (for example, books -
    book, looked - look). The main two algorithms are:

    - Porter stemming algorithm: removes common morphological and inflexional
        endings from words, used here (nltk.stem.PorterStemmer).
    - Lancaster stemming algorithm: a more aggressive stemming algorithm.

    Like lemmatization, stemming reduces inflectional forms to a common base
    form. As opposed to lemmatization, stemming simply chops off inflections.

    :param word: Word to stemm
    :type word: str
    :return: Normalized word
    :rtype word: str
    """

    """
    TODO: If we set this on module level instead, does that save memory
    (=speed)?
    """
    stemmer = PorterStemmer()

    return stemmer.stem(word)


def lemmatize(word: str) -> str:
    """
    Lemmatize a word, using a lexical knowledge bases to get the correct base
    forms of a word.

    Like stemming, lemmatization reduces inflectional forms to a common base
    form. As opposed to stemming, lemmatization does not simply chop off
    inflections. Instead it uses lexical knowledge bases to get the correct
    base forms of words.

    :param word: Word to normalize
    :type word: str
    :return: Normalized word
    :rtype word: str
    """

    """
    TODO: If we set this on module level instead, does that save memory
    (=speed)?
    """
    lemmatizer = WordNetLemmatizer()

    return lemmatizer.lemmatize(word)


def preprocess_word(
    word: str, preprocess_type: PreprocessWordType = PreprocessWordType.NONE
) -> str:
    """
    Preprocess a word by applying different treatments
    e.g. normalization, stemming, lemmatization.

    :param word: Word
    :type word: str
    :param preprocess_type: normalize, normalize and stem, normalize
        and lemmatize, none (default)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Preprocessed word
    :rtype: str
    """

    if preprocess_type == PreprocessWordType.NORMALIZE:
        normalized_word = normalize(word)
        preprocessed_word = normalized_word

    elif preprocess_type == PreprocessWordType.STEM:
        normalized_word = normalize(word)
        preprocessed_word = stem(normalized_word)

    elif preprocess_type == PreprocessWordType.LEMMATIZE:
        normalized_word = normalize(word)
        preprocessed_word = lemmatize(normalized_word)

    elif preprocess_type == PreprocessWordType.NORMALIZE_NUM:
        normalized_word = normalize_including_numbers(word)
        preprocessed_word = normalized_word

    else:  # PreprocessWordType.NONE or unknown
        preprocessed_word = word

    return preprocessed_word


def longsfix_sentence(sentence: str, defoe_path: str, os_type: str):
    """
    Unsure of what this function does; leaving it private for docs for now.

    :meta private:
    """

    if "'" in sentence:
        sentence = sentence.replace("'", "'\\''")

    cmd = (
        "printf '%s' '"
        + sentence
        + "' | "
        + defoe_path
        + "defoe/long_s_fix/"
        + os_type
        + "/lxtransduce -l spelling="
        + defoe_path
        + "defoe/long_s_fix/f-to-s.lex "
        + defoe_path
        + "defoe/long_s_fix/fix-spelling.gr"
    )

    try:
        proc = subprocess.Popen(
            cmd.encode("utf-8"),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()

        if "Error" in str(stderr):
            print("---Err: '{}'".format(stderr))
            stdout_value = sentence
        else:
            stdout_value = stdout

        fix_s = stdout_value.decode("utf-8").split("\n")[0]
    except:  # TODO: Change bare excepts to explicit
        fix_s = sentence
    if re.search("[aeiou]fs", fix_s):
        fix_final = re.sub("fs", "ss", fix_s)
    else:
        fix_final = fix_s
    return fix_final


def spacy_nlp(
    text: str, lang_model: str = "en_core_web_sm"
) -> spacy.tokens.doc.Doc:
    """
    Loads SpaCy with a given language model and runs its ``nlp`` function on
    the given text.

    :param text: The text for which you want to create a
        ``spacy.tokens.doc.Doc``.
    :type text: str
    :param lang_model: Language model to apply, defaults to ``en_core_web_sm``
    :type lang_model: str
    :return: A SpaCy container for accessing linguistic annotations
    :rtype: spacy.tokens.doc.Doc
    """

    try:
        nlp = spacy.load(lang_model)
    except OSError:
        raise OSError("Language model cannot be found.")

    doc = nlp(text)

    return doc


def serialize_doc(
    doc: spacy.tokens.doc.Doc, lang_model: str = "en"
) -> tuple[bytes, bytes]:
    """
    Serializes a given SpaCy container for accessing linguistic annotations.

    :param doc: A SpaCy container for accessing linguistic annotations
    :type doc: spacy.tokens.doc.Doc
    :param lang_model: Language model to apply, defaults to ``en``
    :type lang_model: str
    :return: A tuple consisting of two bytes values: one for the SpaCy
        container for accessing linguistic annotations, the other for the
        storage class for SpaCy's vocabulary
    :rtype: spacy.tokens.doc.Doc
    """

    nlp = spacy.load(lang_model)
    vocab_bytes = nlp.vocab.to_bytes()
    doc_bytes = doc.to_bytes()
    return doc_bytes, vocab_bytes


def serialize_spacy(
    text: str, lang_model: str = "en_core_web_sm"
) -> list[bytes, bytes]:
    """
    Serializes a given SpaCy container for accessing linguistic annotations
    and a storage class for SpaCy's vocabulary, based on a given text.

    :param text: The text for which you want to create a
        ``spacy.tokens.doc.Doc`` which will be serialized through the function
    :type text: str
    :param lang_model: Language model to apply, defaults to ``en_core_web_sm``
    :type lang_model: str
    :return: A list consisting of two bytes values: one for the SpaCy
        container for accessing linguistic annotations, the other for the
        storage class for SpaCy's vocabulary
    :rtype: list[bytes, bytes]
    """

    doc = spacy_nlp(text=text, lang_model=lang_model)
    doc_bytes, vocab_bytes = serialize_doc(doc, lang_model=lang_model)
    return [doc_bytes, vocab_bytes]


def deserialize_doc(serialized_bytes: tuple[bytes, bytes]):
    """
    Deserializes a given SpaCy container for accessing linguistic annotations.

    :param serialized_bytes: A tuple of two serialized bytes lengths
        representing a SpaCy container for accessing linguistic annotations
        and a storage class for SpaCy's vocabulary
    :type serialized_bytes: tuple[bytes, bytes]
    :return: SpaCy container for accessing linguistic annotations
    :rtype: spacy.tokens.doc.Doc
    """
    vocab = Vocab()
    doc_bytes = serialized_bytes[0]
    vocab_bytes = serialized_bytes[1]
    vocab.from_bytes(vocab_bytes)
    doc = Doc(vocab).from_bytes(doc_bytes)
    return doc


def display_spacy(doc: spacy.tokens.doc.Doc):
    """
    For a given SpaCy container for accessing linguistic annotations, this
    function will display its entities, if the container has any.

    :param doc: SpaCy container for accessing linguistic annotations
    :type doc: spacy.tokens.doc.Doc
    :return: True
    :rtype: bool
    """
    if doc.ents:
        spacy.displacy.render(doc, style="ent")
    return True


def spacy_entities(
    doc: spacy.tokens.doc.Doc,
) -> list[tuple[spacy.tokens.span.Span, str, int]]:
    """
    Returns a list of the SpaCy recognised entities in a given SpaCy container
    for accessing linguistic annotations.

    :param doc: SpaCy container for accessing linguistic annotations
    :type doc: spacy.tokens.doc.Doc
    :return: A list of tuples consisting of a SpaCy span (see
        spacy.tokens.span.Span, a string representation of the label and an
        integer representing the label)
    :rtype: list[tuple[spacy.tokens.span.Span, str, int]]
    """
    return [(i, i.label_, i.label) for i in doc.ents]


def xml_geo_entities(doc: spacy.tokens.doc.Doc) -> tuple[int, str]:
    """
    Returns XML for placenames for toponyms in a given SpaCy container for
    accessing linguistic annotations, and a flag for whether placenames have
    been detected in the container by SpaCy.

    :param doc: SpaCy container for accessing linguistic annotations
    :type doc: spacy.tokens.doc.Doc
    :return: A tuple consisting of a flag indicating whether placenames have
        been detected and a string with XML of placenames.
    :rtype: tuple[int, str]
    """
    id = 0
    xml_doc = "<placenames> "
    flag = 0
    for ent in doc.ents:
        if ent.label_ == "LOC" or ent.label_ == "GPE":
            id = id + 1
            toponym = ent.text
            child = '<placename id="' + str(id) + '" name="' + toponym + '"/> '
            xml_doc = xml_doc + child
            flag = 1
    xml_doc = xml_doc + "</placenames>"
    return flag, xml_doc


def xml_geo_entities_snippet(
    doc: spacy.tokens.doc.Doc,
) -> tuple[int, str, dict]:
    """
    :param doc: SpaCy container for accessing linguistic annotations
    :type doc: spacy.tokens.doc.Doc
    :return: A tuple consisting of a flag indicating whether placenames have
        been detected and a string with XML of placenames and a dictionary
        with a key identifier and a snippet of -5/+5 words around the
        identified placename.
    :rtype: tuple[int, str, dict]
    """
    snippet = {}
    id = 0
    xml_doc = "<placenames> "
    flag = 0
    index = 0
    for token in doc:
        if token.ent_type_ == "LOC" or token.ent_type_ == "GPE":
            id = id + 1
            toponym = token.text
            child = '<placename id="' + str(id) + '" name="' + toponym + '"/> '
            xml_doc = xml_doc + child
            flag = 1
            left_index = index - 5
            if left_index <= 0:
                left_index = 0

            right_index = index + 6
            if right_index >= len(doc):
                right_index = len(doc)

            left = doc[left_index:index]
            right = doc[index + 1 : right_index]
            snippet_er = ""
            for i in left:
                snippet_er += i.text + " "
            snippet_er += token.text + " "
            for i in right:
                snippet_er += i.text + " "

            snippet_id = toponym + "-" + str(id)
            snippet[snippet_id] = snippet_er
        index += 1
    xml_doc = xml_doc + "</placenames>"
    return flag, xml_doc, snippet


def georesolve_cmd(in_xml, defoe_path, gazetteer, bounding_box) -> str:
    """
    Function where Rosa used ``geoground`` script for georesolving placenames
    in XML.

    :meta private:
    """
    georesolve_xml = ""
    attempt = 0
    flag = 1
    if "'" in in_xml:
        in_xml = in_xml.replace("'", "'\\''")

    cmd = (
        "printf '%s' '"
        + in_xml
        + "' | "
        + defoe_path
        + "georesolve/scripts/geoground -g "
        + gazetteer
        + " "
        + bounding_box
        + " -top"
    )
    while (len(georesolve_xml) < 5) and (attempt < 1000) and (flag == 1):
        proc = subprocess.Popen(
            cmd.encode("utf-8"),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        if "Error" in str(stderr):
            flag = 0
            print("err: '{}'".format(stderr))
            georesolve_xml = ""
        else:
            if stdout == in_xml:
                georesolve_xml = ""
            else:
                georesolve_xml = stdout
        attempt += 1
    return georesolve_xml


def coord_xml(geo_xml: str) -> dict:
    """
    Function connected to georesolve_cmd above, which generates a dictionary
    with a toponym name and ID as key and its values are tuples consisting of,
    among other things, latitude and longitude values.

    :meta private:
    """
    dResolvedLocs = {}
    if len(geo_xml) > 5:
        root = etree.fromstring(geo_xml)
        for child in root:
            toponym_name = child.attrib["name"]
            toponym_id = child.attrib["id"]
            latitude = ""
            longitude = ""
            pop = ""
            in_cc = ""
            type = ""
            if len(child) >= 1:
                for subchild in child:
                    if "lat" in subchild.attrib:
                        latitude = subchild.attrib["lat"]
                    if "ling" in subchild.attrib:
                        longitude = subchild.attrib["long"]
                    if "pop" in subchild.attrib:
                        pop = subchild.attrib["pop"]
                    if "in-cc" in subchild.attrib:
                        in_cc = subchild.attrib["in-cc"]
                    if "type" in subchild.attrib:
                        type = subchild.attrib["type"]
                    dResolvedLocs[toponym_name + "-" + toponym_id] = (
                        latitude,
                        longitude,
                        pop,
                        in_cc,
                        type,
                    )
        dResolvedLocs[toponym_name + "-" + toponym_id] = (
            latitude,
            longitude,
            pop,
            in_cc,
            type,
        )
    else:
        dResolvedLocs["cmd"] = "Problems!"
    return dResolvedLocs


def coord_xml_snippet(geo_xml: str, snippet: dict):
    """
    Same as ``coord_xml`` above but here joined with snippet (generated
    by ``xml_geo_entities_snippet`` above) which generates a dictionary,
    which values includes the snippet around the coordinates.

    :meta private:
    """
    dResolvedLocs = {}
    if len(geo_xml) > 5:
        root = etree.fromstring(geo_xml)
        for child in root:
            toponymName = child.attrib["name"]
            toponymId = child.attrib["id"]
            latitude = ""
            longitude = ""
            pop = ""
            in_cc = ""
            type = ""
            snippet_id = toponymName + "-" + toponymId
            snippet_er = snippet[snippet_id]

            if len(child) >= 1:
                for subchild in child:
                    if "lat" in subchild.attrib:
                        latitude = subchild.attrib["lat"]
                    if "long" in subchild.attrib:
                        longitude = subchild.attrib["long"]
                    if "pop" in subchild.attrib:
                        pop = subchild.attrib["pop"]
                    if "in-cc" in subchild.attrib:
                        in_cc = subchild.attrib["in-cc"]
                    if "type" in subchild.attrib:
                        type = subchild.attrib["type"]
                    snippet_id = toponymName + "-" + toponymId
                    snippet_er = snippet[snippet_id]
                    dResolvedLocs[snippet_id] = {
                        "lat": latitude,
                        "long": longitude,
                        "pop": pop,
                        "in-cc": in_cc,
                        "type": type,
                        "snippet": snippet_er,
                    }
        dResolvedLocs[snippet_id] = {
            "lat": latitude,
            "long": longitude,
            "pop": pop,
            "in-cc": in_cc,
            "type": type,
            "snippet": snippet_er,
        }
    else:
        dResolvedLocs["cmd"] = "Georesolver_Empty"
    return dResolvedLocs


def geomap_cmd(in_xml, defoe_path, os_type, gazetteer, bounding_box):
    """
    Another georesolving function that uses ``geoground``.

    :meta private:
    """
    geomap_html = ""
    attempt = 0
    if "'" in in_xml:
        in_xml = in_xml.replace("'", "'\\''")
    cmd = (
        "printf '%s' '"
        + in_xml
        + " ' | "
        + defoe_path
        + "georesolve/scripts/geoground -g "
        + gazetteer
        + " "
        + bounding_box
        + " -top | "
        + defoe_path
        + "georesolve/bin/"
        + os_type
        + "/lxt -s "
        + defoe_path
        + "georesolve/lib/georesolve/gazmap-leaflet.xsl"
    )

    while (len(geomap_html) < 5) and (attempt < 1000):
        proc = subprocess.Popen(
            cmd.encode("utf-8"),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        geomap_html = proc.communicate(timeout=100)[0]
        attempt += 1
    return geomap_html.decode("utf-8")


def geoparser_cmd(text, defoe_path, os_type, gazetteer, bounding_box):
    """
    Another georesolving function that uses ``geoparser-v1.1`` and
    ``georesolve``.

    :meta private:
    """
    attempt = 0
    flag = 1
    geoparser_xml = ""
    if "'" in text:
        text = text.replace("'", "'\\''")

    cmd = (
        "echo '%s' '"
        + text
        + "' | "
        + defoe_path
        + "geoparser-v1.1/scripts/run -t plain -g "
        + gazetteer
        + " "
        + bounding_box
        + " -top | "
        + defoe_path
        + "georesolve/bin/"
        + os_type
        + "/lxreplace -q s | "
        + defoe_path
        + "geoparser-v1.1/bin/"
        + os_type
        + "/lxt -s "
        + defoe_path
        + "geoparser-v1.1/lib/georesolve/addfivewsnippet.xsl"
    )

    while (len(geoparser_xml) < 5) and (attempt < 1000) and (flag == 1):
        proc = subprocess.Popen(
            cmd.encode("utf-8"),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        if "Error" in str(stderr):
            flag = 0
            print("err: '{}'".format(stderr))
        else:
            geoparser_xml = stdout
        attempt += 1
    return geoparser_xml


def geoparser_coord_xml(geo_xml):
    """
    :meta private:
    """
    dResolvedLocs = dict()
    try:
        root = etree.fromstring(geo_xml)
        for element in root.iter():

            if element.tag == "ent":
                if element.attrib["type"] == "location":
                    latitude = element.attrib["lat"]
                    longitude = element.attrib["long"]
                    toponymId = element.attrib["id"]
                    if "in-country" in element.attrib:
                        in_cc = element.attrib["in-country"]
                    else:
                        in_cc = ""
                    if "pop-size" in element.attrib:
                        pop = element.attrib["pop-size"]
                    else:
                        pop = ""
                    if "feat-type" in element.attrib:
                        type = element.attrib["feat-type"]
                    else:
                        type = ""
                    if "snippet" in element.attrib:
                        snippet_er = element.attrib["snippet"]
                    else:
                        snippet_er = ""
                    for subchild in element:
                        if subchild.tag == "parts":
                            for subsubchild in subchild:
                                toponymName = subsubchild.text
                                # print(toponymName, latitude, longitude)
                                dResolvedLocs[
                                    toponymName + "-" + toponymId
                                ] = {
                                    "lat": latitude,
                                    "long": longitude,
                                    "pop": pop,
                                    "in-cc": in_cc,
                                    "type": type,
                                    "snippet": snippet_er,
                                }
    except:  # TODO: Change bare excepts to explicit
        pass
    return dResolvedLocs


def geoparser_text_xml(geo_xml):
    """
    :meta private:
    """
    text_ER = []
    try:
        root = etree.fromstring(geo_xml)
        for element in root.iter():
            if element.tag == "text":
                for subchild in element:
                    if subchild.tag == "p":
                        for subsubchild in subchild:
                            for subsubsubchild in subsubchild:
                                if subsubsubchild.tag == "w":
                                    inf = {}
                                    inf["p"] = subsubsubchild.attrib["p"]
                                    inf["group"] = subsubsubchild.attrib[
                                        "group"
                                    ]
                                    inf["id"] = subsubsubchild.attrib["id"]
                                    inf["pws"] = subsubsubchild.attrib["pws"]
                                    if (
                                        "locname"
                                        in subsubsubchild.attrib.keys()
                                    ):
                                        inf["locname"] = subsubsubchild.attrib[
                                            "locname"
                                        ]
                                    text_ER.append((subsubsubchild.text, inf))

    except:  # TODO: Change bare excepts to explicit
        pass
    return text_ER


def create_es_index(es_index, force_creation):
    """
    Create specified ElasticSearch index if it doesn't already exist.

    :param es_index: the name of the ES index
    :type es_index: TODO
    :param force_creation: delete the original index and create a brand new
        index
    :type force_creation: bool
    :return: Boolean representing whether the index was created or not
    :rtype: bool
    """
    created = False
    es_index_settings = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "settings.TITLE": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.AUTHOR": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.EDITION": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.YEAR": {
                    "type": "text",
                    "fields": {"date": {"type": "date", "format": "yyyy"}},
                },
                "settings.PLACE": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.ARCHIVE_FILENAME": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.SOURCE_TEXT_FILENAME": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.TEXT_UNIT": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.TEXT_UNIT_ID": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.NUM_TEXT_UNIT": {
                    "type": "long",
                },
                "settings.TYPE_ARCHIVE": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.MODEL": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.SOURCE_TEXT_CLEAN": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "settings.NUM_WORDS": {
                    "type": "text",
                    "fields": {"integer": {"type": "integer"}},
                },
                "settings.BOOK_ID": {
                    "type": "text",
                    "fields": {"integer": {"type": "integer"}},
                },
                "misc": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
            }
        },
    }
    try:
        # Overwrite without checking if force param supplied
        if force_creation:
            # Explicitly delete in this case
            if Elasticsearch.get_instance().indices.exists(es_index):
                Elasticsearch.get_instance().indices.delete(index=es_index)
            # Ignore 400 means to ignore "Index Already Exist" error.
            Elasticsearch.get_instance().indices.create(
                index=es_index, ignore=400, body=es_index_settings
            )
            # self.es.indices.create(index=es_index, ignore=400)
            created = True
        else:
            # Doesn't already exist so we can create it
            Elasticsearch.get_instance().indices.create(
                index=es_index, ignore=400, body=es_index_settings
            )
            created = True
    except Exception as ex:
        print("Error creating %s: %s" % (es_index, ex))
    finally:
        return created


def get_config(config_file: str, optional=False):
    """
    This function attempts to open a configuration file. If ``optional`` is
    set to ``True`` and no (valid) configuration file can be found, it will
    return an empty dictionary rather than crashing.

    :param config_file: Path to a configuration file
    :type config_file: str
    :param optional: Whether a file is required or optional, defaults to
        ``False``
    :type optional: bool
    :raises FileNotFoundError: If the configuration file cannot be found and
        ``optional`` is set to ``False``
    :raises SyntaxError: If the configuration file path was not provided as
        string
    :return: A configuration dictionary
    :rtype: dict
    """
    if not isinstance(config_file, str):
        raise SyntaxError(
            f"The name of the configuration file must be provided as a string. (Current value: {config_file}.)"  # noqa
        )

    try:
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        if optional:
            return {}

        raise FileNotFoundError(e)


def get_normalized_keywords(
    config_file: str,
    preprocess_type: PreprocessWordType = PreprocessWordType.NONE,
) -> list[str]:
    """
    Extracts the keywords from a configuration file and normalizes them
    according to a provided preprocessing type parameter.

    :param config_file: Path to a configuration file
    :type config_file: str
    :return: A list of processed keywords
    :rtype: list[str]
    """

    with open(config_file, "r") as f:
        if preprocess_type:
            return [preprocess_word(word, preprocess_type) for word in list(f)]
        else:
            return [normalize(word) for word in list(f)]
