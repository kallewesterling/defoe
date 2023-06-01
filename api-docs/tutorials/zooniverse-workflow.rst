Zooniverse Workflow
===================

..
  TODO
  A tutorial that shows the zooniverse workflow
  query -> extract -> manifest -> upload process

  QUERY

  1. After setting up a Defoe VM + Notebook, you open a new notebook.

  2. Make sure notebook is connected to Azure and loads the correct Archives:

      .. code-block: python

        from azure.storage.blob import ContainerClient, BlobServiceClient

        sas_url_container = "https://lwmnewspapers.blob.core.windows.net/lwmnewspapers?sv=2020-08-04&ss=... (etc)"
        sas_url_connection_string = "BlobEndpoint=https://lwmnewspapers.blob.core.windows.net/;QueueEndpoint=... (etc)"

        container_client = ContainerClient.from_container_url(sas_url_container)
        blob_service_client = BlobServiceClient.from_connection_string(sas_url_connection_string)

    In order for us to load particular papers:

      .. code-block: python

        paper_keys = ['0000188', '0000231', '0000234', '0000237', '0000246', '0000364', '0000425', '0000496', '0000601', '0000605', '0002598', '0000743', '0001604', '0001605', '0001722', '0001723', '0001749', '0001750', '0001886', '0001887', '0000425', '0001888', '0001890', '0000605', '0001891', '0001892', '0001893', '0002452', '0002453', '0002454', '0002455', '0002456', '0002457', '0002541', '0002542', '0002575', '0002595', '0002596', '0002597', '0002622', '0002623', '0002624', '0002636', '0002657', '0002688', '0002765', '0002772', '0002773', '0002774', '0002775', '0000236', '0002785', '0002829', '0002830', '0003003', '0003004', '0003005', '0003006', '0003007', '0000625', '0003234', '0003240', '0003420', '0003768', '0003769', '0003771', '0003772', '0003773', '0003774', '0003775', '0003776', '0003777', '0003778', '0003794', '0003870', '0004707', '0004708', '0004709', '0004710', '0004935', '0004936', '0004952', '0000624', '0005046', '0005101', '0005102', '0005103', '0005104', '0005105', '0005106', '0005386', '0005402', '0005431', '0005432', '0005671', '0005889', '0005890', '0005891', '0005892', '0006073', '0006074', '0006568', '0006569', '0006570', '0006571', '0006572', '0006573', '0006574', '0006575', '0006576', '0006577', '0006578', '0006579', '0006580', '0006581', '0006582', '0006583', '0007476', '0007527', '0007528', '0007529', '0007530', '0007531', '0007532', '0007533', '0007534', '0007535', '0007536', '0007537', '0007538', '0007539', '0007540', '0007541', '0007542', '0007543', '0007544', '0007545', '0007546', '0007547', '0007548', '0007549', '0007550', '0007551', '0007552', '0007553', '0007554', '0007555', '0007556', '0007557', '0007558', '0007559', '0007560', '0007561', '0007562', '0007563', '0007564', '0007565', '0007566', '0007567', '0007568', '0007569', '0007570', '0007571', '0007572', '0007573', '0007575', '0007576', '0007577', '0007578', '0007579', '0007580', '0007581', '0007582', '0007583', '0007584', '0008030', '0008266', '0008293', '0009145', '0009158', '0009159', '0009160', '0009528', '0009536', '0009537', '0009874', '0009875', '0009876', '0009877', '0009878', '0009879', '0009881', '0009969', '0010177', '0010178', '0010179', '0010180', '0010181', '0010182', '0010781', '0010809', '0010811', '0010965', '0010966', '0011029', '0011138', '0011139', '0011140', '0011141', '0011142', '0011143', '0011144', '0011145', '0011147', '0011147', '0011148', '0011149', '0011150', '0011151', '0011152', '0011155', '0011156', '0011157', '0011158', '0011159', '0011160', '0011161', '0011162', '0011163', '0011164', '0011165', '0011166', '0011167', '0011168', '0011169', '0011170', '0011171', '0011172', '0011173', '0011174', '0014584', '0014585', '0014586', '0014587', '0014588', '0014589', '0014590', '0014923', '0014964', '0014965', '0014966', '0014967', '0014968', '0014969', '0014970', '0014971', '0015020', '0015280', '0015281', '0015282', '0015283', '0015301', '0015302', '0015303', '0015391', '0015392', '0015393', '0015394', '0015623', '0015624', '0015625', '0015626', '0015627', '0015628', '0015629', '0015630', '0015632', '0015633', '0015634', '0015635', '0015636', '0015643', '0015644', '0015645', '0015646', '0015647', '0015648', '0015649', '0015650', '0015671', '0015672', '0015673', '0015783', '0015784', '0015785', '0015786', '0015787', '0015788', '0015789', '0015790', '0015791', '0015792', '0015859', '0015860', '0015861', '0015862', '0015863', '0015864', '0015865', '0015866', '0016397', '0016398', '0016399', '0016400', '0016401', '0016481', '0016503', '0016506', '0016507', '0022913', '0022925', '0023162', '0003768', '0023220', '0023243', '0023244', '0023373', '0023540', '0023611', '0023761', '0023762', '0024017', '0000601', '0000629', '0024553', '0024590', '0024591', '0024625', '0001065', '0024702', '0024757', '0001078', '0024839', '0025002', '0025802', '0025803', '0025804', '0025805', '0026031', '0032882', '0032953', '0001119', '0033299', '0024839', '0101091', '0033319', '0033319', '0000740', '0001119', '0033374', '0033437', '0033438', '0000789', '0000813', '0001078', '0001065', '0001123', '0000496', '0033550', '0000941', '0033612', '0033616', '0033617', '0033806', '0100373', '0033861', '0100243', '0100600', '0100676']
        blobs = [b for paper_key in paper_keys for b in container_client.list_blobs(name_starts_with=paper_key)]

        file_count = len(blobs)
        paper_count = len(set([x['name'].split('/')[0] for x in blobs]))

        print(f"A total of {file_count} files were found, across {paper_count} papers")

    Ensure correct years are loaded as file paths

      .. code-block: python

        def passes_year(folder):
          year = Path(folder).parent.stem

          # before and including 1882
          return int(year) < 1883

        issue_folders = list(set(str(Path(blob.name).parent) for blob in blobs))

        issue_count = len(issue_folders)
        paper_count = len(set([x.split('/')[0] for x in issue_folders]))

        print(f"{issue_count} issues after filtering for relevant papers. Issues come from {paper_count} papers")

        issue_folders_filtered_by_year = [folder for folder in issue_folders if passes_year(folder)]

        issue_count = len(issue_folders_filtered_by_year)
        paper_count = len(set([x.split('/')[0] for x in issue_folders_filtered_by_year]))

        print(f"{issue_count} issues after filtering for years. Issues come from {paper_count} papers")

        # Get filepaths from filtering by year
        filepaths = [f'{local_blobstore}{folder}' for folder in issue_folders_filtered_by_year]

  3. Creating a query can be done in two different ways: (a) pre-constructed queries (do_query functions) or (b) custom queries. Here's how you do a pre-constructed query:

      3a. First write your settings:

          .. code-block: python

              %%writefile settings.yml

              preprocess: lemmatize
              data: targets.txt
              years_filter: 1780-1918 # does not affect this query since we've already separated it out by filename....
              output_path: /home/kallewesterling/images/
              highlight: True
              fuzzy_target: False
              fuzzy_keyword: False

      3b. Write your targets:

          .. code-block: python

              %%writefile targets.txt

              targets:
                  - engine

              keywords:
                  - accident
                  - amputated
                  - bone
                  - broke
                  - bruise
                  - burns
                  - burned
                  - collision
                  - collide
                  - collided
                  - crush
                  - crushed
                  - damage
                  - damaged
                  - dangerous
                  - death
                  - dead
                  - deceased
                  - died
                  - disaster
                  - explode
                  - exploded
                  - explosion
                  - extricated
                  - fall
                  - fell
                  - fatal
                  - fence
                  - fire
                  - guard
                  - hurt
                  - incident
                  - infirmary
                  - injury
                  - injured
                  - mutilate
                  - mutilated
                  - negligence
                  - perish
                  - perished
                  - pulp
                  - pulverised
                  - rip
                  - ripped
                  - sever
                  - severed
                  - smashed
                  - trapped
                  - wound
                  - wounded

      3c. Run and save results from the query

          .. code-block: python

              # First, parallelize the archives
              a = sc.parallelize([Archive(path) for path in filepaths])

              # Second, yield the results
              results = do_query(a, config_file='settings.yml')

              # Third, save the results
              results_json = json.dumps(results)
              Path('results.json').write_text(results_json)

  4. Optional, if you want to custom-write your query, here's how you do it...

      4a. First write your query, which should take an RDD of Archives as its first argument and should return any valid Python data type (like a list or dictionary):

          This example code returns a list of tuples consisting of the textblock's ID and its tokens for each TextBlock that contains "string" in its content.

          .. code-block: python

              def do_query(archives_rdd=None, *args, **kwargs):
                  # first extract the documents from the archive
                  documents = archives.flatMap(
                      lambda archive: [document for document in list(archive)]
                  )

                  # second, get matching documents
                  def get_matches(document):
                      matches = []
                      for textblock in document.textblocks:
                          if "string" in textblock.content:
                              matches.append((textblock.id, textblock.tokens))

                      return matches

                  matches = documents.flatMap(
                      lambda document: get_matches(document)
                  )

                  # third, collect the results and return them
                  matches.collect()

                  return results

      4b. Run and save results from the query via ``sc``, the SparkContext which should be available in your notebook

          .. code-block: python

              a = sc.parallelize([Archive(path) for path in filepaths])
              matches = do_query(archive)
              Path("results.json").write_text(json.dumps(matches))

  EXTRACT IMAGES

  We separate out this task as Spark is (supposedly) faster to use for querying, and once we have the results, it's easy to go in and do a multiprocess, for instance, of the I/O of processing images:

  (Note: You _could_ add an image-saving routine in the ``get_matches`` function above. I haven't tested it, and it might be a solution. The textblock, for instance, has the ``.image`` attribute, so it's easy to access and save to a file somewhere...)

  