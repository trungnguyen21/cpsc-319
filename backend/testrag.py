from google.cloud import discoveryengine_v1alpha as discoveryengine

client = discoveryengine.SearchServiceClient()
serving_config = client.serving_config_path(
    project="benevity-impact-project",
    location="global",
    data_store="nonprofit-reports-ds_1771732645614",
    serving_config="default_search"
)

request = discoveryengine.SearchRequest(
    serving_config=serving_config,
    query="Red Cross wildfire",
    page_size=3,
    content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
        search_result_mode=discoveryengine.SearchRequest.ContentSearchSpec.SearchResultMode.CHUNKS,
        chunk_spec=discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec(
            num_previous_chunks=1,
            num_next_chunks=1,
        ),
    ),
)

response = client.search(request)
print(f"Total: {response.total_size}")
for r in response.results:
    print("--- RESULT ---")
    print(f"chunk: '{r.chunk}'")
    print(f"chunk content: '{getattr(r.chunk, 'content', 'NO CONTENT ATTR')}'")
    print(f"struct keys: {list(r.document.derived_struct_data.keys())}")