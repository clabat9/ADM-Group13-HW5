
# coding: utf-8

from collections import defaultdict
import pandas as pd
import networkx as nx
import numpy as np
import itertools as it
import pickle
from collections import *
from operator import itemgetter
import statistics
import math

# SECTION 1: GRAPH CREATION ----------

# This class creates a graph from a file containing pair of edges.
class Graph_gen:
    
    def __init__(self,path):
        with open(path,'r') as f:
            f = f.read().split('\n')
            self.graph = defaultdict(list) # This is the adjacency list
            for row in f:
                self.link=row.split('\t')
                try:
                    self.graph[int(self.link[0])].append(int(self.link[1])) # It's updated for each row of the file {first column: source, second column: destination}
                    if int(self.link[1]) not in self.graph.keys(): #  We've to take in account all nodes, so also the source will have a slot in the dic, maybe with an empty associated list if they have only incoming edges
                        self.graph[int(self.link[1])] = []
                except: True
        
        # Just computing some infos about the graph. Very intuitive.
        self.nodes = len(self.graph)
        self.edges = sum([len(self.graph[node]) for node in self.graph])
        self.is_dir = self.is_directed(self.graph)
        self.avg_degree = 2*self.edges/self.nodes
        self.density = 2*self.edges/(self.nodes*(self.nodes -1))
        
     
    # This method determines if the graph is directed by checking if there is a pair of edges in different direction for each pair of node. If one pair misses, the graph is directed.
    def is_directed(self,graph):
        for el in graph:
            dir_ = all([el in graph[edge] for edge in graph[el]])
            if not dir_ :
                return(not dir_)
            
        return(dir_)
    
    
    
    
    
    
    
    
    
# SECTION 2: BLOCK RANKING ----------

# This functions cleans the categories by cutting the ones under 3500 elements and
# all the nodes that are not in the reduced graph.
def cat_clean(path,graph): 
    e = set(graph.nodes()) # Nodes that are present
    with open(path, 'r') as document:
        cat = {}
        for line in document:
            line = line.split()
            if len(line)>3500:
                all_nodes = set(map(int,line[1:]))
                present_nodes = e.intersection(all_nodes) # We need only the present ones.
                cat[line[0].replace('Category:','').replace(';','')] = list(present_nodes)
    return cat





# This function implements the bfs by returning a dic indexed by node and containing the distance from the root node. Not too much to comment, standar implementation with queue.
def bfs(graph, root):
    seen, queue = {root}, ct.deque([(root, 0)])
    levels = {}
    
    while queue:
        vertex, level = queue.popleft()
   
        levels[vertex] = level
        for node in graph.get(vertex, []):
            if node not in seen:
                seen.add(node)
                queue.append((node, level + 1))
    return levels




# This function creates an inverted index of the form {node: category of the node}.
def cat_inverted_index(cat):
    inverted_index = {}
    for el in cat:
        for node in cat[el]:
            inverted_index[node] = el
    return inverted_index



# This function implements the block ranking.
def block_ranking(cat,input_cat,inverted_index,graph):
    block_rank= defaultdict(list) # This def dic will contain { category: [shortest paths belonging to the category]}
    nodes = defaultdict(set) # This def dic is pretty important becouse takes in account the visited nodes of the categories, in order to get the non paths values. It is in the form { category : {visited nodes}}
    for node in cat[input_cat]: # For every node of C_0
        tree = bfs(graph,node) # Computes the BFS
        for node in tree: # For every visited nodes
            cat_ = inverted_index[node] # catches the category
            block_rank[cat_].append(tree[node]) # Updates the ranking dic
            nodes[cat_].add(node) # Updates the visited nodes dic
    
    
    # The following code computes the score
    score = {} # Dictionary that will contain the scores { category : score}
    for el in block_rank: # For every category
        inf_number = math.log10(10 + len(cat[el])-len(nodes[el])) # Gets the number of inf by subtracting the number of visited nodes to the total number of nodes in the category and applies the explained formula
        score[el] = statistics.median(block_rank[el])*inf_number # Gets the score
    
    
    # Sets to zero the input_category
    score[input_cat] = 0 
    # Sorts the dic
    score = sorted(score.items(), key=lambda kv: kv[1])
        
        
    return(score)









# SECTION 3: NODE RANKING ----------


# This functions implements the node ranking
def node_ranking(s,G, rank):
        # For each category, it creates the induced subgraph and assigns the initial weights
        node_ranking=[]
        for i in rank :
            sub=G.subgraph(s[i])
            temp=defaultdict(int)
            for node in sub.nodes():
                temp[node]=sub.degree(node)
            node_ranking.append(temp)
        
        # For each node of the subgraphs it updates the weights by checking 
        # the weights of its predecessors
        for i in range(1,len(node_ranking)):
            for node in node_ranking[i]:
                for predecessor in G.predecessors(node):
                    node_ranking[i][node] += node_ranking[i-1][predecessor]
         
        # Creates a dic of the form { category : {node : sum of the weigths}}
        node_ranking_final={}
        for i in node_ranking:
            for category in s:
                node_ranking_final[category]=dict(i)
        
        # Creates the final sorted by sum of the weights dic of the form
        # {category : [(node, sum of the wights)]}
        node_ranking_final_sorted={}
        for k,v in node_ranking_final.items():
            order=sorted(v.items(), key=itemgetter(1),reverse=True)
            node_ranking_final_sorted[k]=order
        return node_ranking_final
    
    
    
# This function matches the number of nodes with the name of the article and 
# returns the overall node ranking as a data frame
def name_matching(rank, path):
    overall = { j :rank[el][j] for el in rank for j in rank[el]} # Flats the dic by deleting the categories level
    with open(path, "r") as f:
        page_names= {}
        for line in f: # And defines a dict of the form {node : name}
            l = line.split()
            page_names[int(l[0])] = " ".join(l[1:])
        
    name_rank = {}
    for i in overall: # in a new dic associates the name of the node with its score
        try:
            name_rank[page_names[i]] = overall[i]
        except:
            name_rank["No-name"+str(i)] = overall[i]
    
    # Sorts the dic and converts it into a data frame
    name_rank = sorted(name_rank.items(), key=lambda kv: kv[1], reverse = True)
    name_rank_ = pd.DataFrame(name_rank, columns=['Article','Scores'])

   
    return name_rank_

    
    

