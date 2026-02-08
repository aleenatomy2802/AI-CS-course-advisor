import logging
import networkx as nx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('journey_map')

class JourneyMap:
    """Creates journey maps for CS courses with NetworkX graph visualization"""
    
    def __init__(self, app=None):
        self.app = app
        self.db = None
        self.Course = None
        self.course_graph = None
        self.course_levels = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        from extensions import db
        from models import Course
        self.db = db
        self.Course = Course
        
        with app.app_context():
            self.build_course_graph()
        logger.info("JourneyMap initialized")

    def build_course_graph(self):
        """Build directed graph of courses with prerequisites"""
        if not self.app:
            return False

        try:
            with self.app.app_context():
                courses = self.Course.query.all()
                if not courses:
                    logger.warning("No courses found")
                    return False
                    
                G = nx.DiGraph()
                
                for course in courses:
                    G.add_node(course.id, 
                             name=course.name, 
                             description=course.description,
                             department=course.department,
                             level=course.level)
                    self.course_levels[course.id] = course.level or 1
                
                from models import CoursePrerequisite
                prereqs = CoursePrerequisite.query.all()
                for prereq in prereqs:
                    G.add_edge(prereq.prerequisite_id, prereq.course_id, relationship="prerequisite")
                
                self.course_graph = G
                logger.info(f"Graph built: {len(G.nodes)} nodes, {len(G.edges)} edges")
                return True
                
        except Exception as e:
            logger.error(f"Error building graph: {e}")
            return False
    
    def get_course_graph_data(self):
        """Return graph in JSON format for visualization"""
        try:
            if not self.course_graph:
                self.build_course_graph()
            
            graph_data = {"nodes": [], "links": []}
            
            for node_id, node_attrs in self.course_graph.nodes(data=True):
                node_data = {"id": node_id}
                node_data.update(node_attrs)
                node_data["level"] = self.course_levels.get(node_id, 1)
                graph_data["nodes"].append(node_data)
            
            for u, v, edge_attrs in self.course_graph.edges(data=True):
                edge_data = {"source": u, "target": v}
                edge_data.update(edge_attrs)
                graph_data["links"].append(edge_data)
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Error generating graph data: {e}")
            return {"nodes": [], "links": []}
    
    def get_prerequisite_chain(self, course_id):
        """Get full prerequisite chain for a course"""
        try:
            if not self.course_graph or course_id not in self.course_graph.nodes:
                return {"nodes": [], "links": []}
            
            prereq_nodes = set()
            prereq_edges = set()
            queue = [course_id]
            visited = set()

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                
                predecessors = list(self.course_graph.predecessors(current))
                for prereq in predecessors:
                    prereq_nodes.add(prereq)
                    prereq_edges.add((prereq, current))
                    if prereq not in visited:
                        queue.append(prereq)

            prereq_nodes.add(course_id)
            
            chain_data = {"nodes": [], "links": []}
            for node_id in prereq_nodes:
                node_attrs = self.course_graph.nodes[node_id]
                node_data = {"id": node_id}
                node_data.update(node_attrs)
                chain_data["nodes"].append(node_data)
            
            for src, dst in prereq_edges:
                edge_attrs = self.course_graph.edges[src, dst]
                chain_data["links"].append({
                    "source": src,
                    "target": dst,
                    "relationship": edge_attrs.get('relationship', 'prerequisite')
                })
            
            return chain_data
            
        except Exception as e:
            logger.error(f"Error getting prerequisite chain: {e}")
            return {"nodes": [], "links": []}
    
    def get_career_pathways(self):
        """Return course progression pathways for careers"""
        return []  # Simplified for deployment
