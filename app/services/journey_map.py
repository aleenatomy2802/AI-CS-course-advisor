"""
Journey Map service — NetworkX graph of course prerequisites.
Single Responsibility: graph building and traversal only.
"""

import logging
import networkx as nx

logger = logging.getLogger('journey_map')


class JourneyMap:
    def __init__(self, app=None):
        self.app = app
        self.course_graph = None
        self.course_levels = {}
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        with app.app_context():
            self.build_course_graph()
        logger.info("JourneyMap initialised")

    # ── Graph construction ────────────────────────────────────

    def build_course_graph(self) -> bool:
        if not self.app:
            return False
        try:
            with self.app.app_context():
                from app.models import Course, CoursePrerequisite

                courses = Course.query.all()
                if not courses:
                    logger.warning("No courses found")
                    return False

                G = nx.DiGraph()
                for c in courses:
                    G.add_node(
                        c.id,
                        name=c.name,
                        description=c.description,
                        department=c.department,
                        level=c.level,
                    )
                    self.course_levels[c.id] = c.level or 1

                for prereq in CoursePrerequisite.query.all():
                    G.add_edge(prereq.prerequisite_id, prereq.course_id,
                               relationship="prerequisite")

                self.course_graph = G
                logger.info(f"Graph built: {len(G.nodes)} nodes, {len(G.edges)} edges")
                return True

        except Exception as e:
            logger.error(f"Error building graph: {e}")
            return False

    # ── Public API ────────────────────────────────────────────

    def get_course_graph_data(self) -> dict:
        try:
            if not self.course_graph:
                self.build_course_graph()

            nodes = [
                {"id": nid, **attrs, "level": self.course_levels.get(nid, 1)}
                for nid, attrs in self.course_graph.nodes(data=True)
            ]
            links = [
                {"source": u, "target": v, **edge_attrs}
                for u, v, edge_attrs in self.course_graph.edges(data=True)
            ]
            return {"nodes": nodes, "links": links}

        except Exception as e:
            logger.error(f"Error generating graph data: {e}")
            return {"nodes": [], "links": []}

    def get_prerequisite_chain(self, course_id: int) -> dict:
        try:
            if not self.course_graph or course_id not in self.course_graph.nodes:
                return {"nodes": [], "links": []}

            prereq_nodes, prereq_edges = set(), set()
            queue, visited = [course_id], set()

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                for prereq in self.course_graph.predecessors(current):
                    prereq_nodes.add(prereq)
                    prereq_edges.add((prereq, current))
                    if prereq not in visited:
                        queue.append(prereq)

            prereq_nodes.add(course_id)

            nodes = [
                {"id": nid, **self.course_graph.nodes[nid]}
                for nid in prereq_nodes
            ]
            links = [
                {
                    "source": src,
                    "target": dst,
                    "relationship": self.course_graph.edges[src, dst].get(
                        'relationship', 'prerequisite'
                    ),
                }
                for src, dst in prereq_edges
            ]
            return {"nodes": nodes, "links": links}

        except Exception as e:
            logger.error(f"Error getting prerequisite chain: {e}")
            return {"nodes": [], "links": []}
