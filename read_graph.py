import json

GRAPH_FILE_NAME = 'graph.json'

def load_cache():
    try:
        graph_file = open(GRAPH_FILE_NAME, 'r')
        graph_content = graph_file.read()
        graph = json.loads(graph_content)
        graph_file.close()
    except:
        print('Cannot open the graph file')
        exit()
    return graph

graph = load_cache()
print(graph)
