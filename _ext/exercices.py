"""
Add directives for writing exercises and solutions. This extension supports:

   .. exercise:: Name

       Any content here...

       .. solution

           Solution takes place here...

To summarize:

    - Exercises are automatically numbered "Exercise 1.1" (section number + exercise number)
    - If a `.. exercises::`, the exercises is mentionned, the `exercise` directive
      is replaced with a reference to the exercise
    - Solutions can be hidden with `:hidden:`
"""
from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Tuple, Union
from docutils.frontend import OptionParser
import sphinx.locale
from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives.admonitions import BaseAdmonition, Hint
from sphinx import addnodes
from sphinx.environment.adapters.toctree import TocTree
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.locale import _
from sphinx.util import logging, status_iterator, url_re
from sphinx.util.console import colorize
from sphinx.util.docutils import SphinxDirective
from sphinx.transforms import SphinxTransform
from sphinx.builders.latex import LaTeXBuilder
from sphinx.writers.latex import LaTeXWriter, LaTeXTranslator
from sphinx.util.docutils import SphinxFileOutput, new_document
from os import path
from sphinx.locale import _, __
from sphinx.util import texescape, logging, progress_message, status_iterator

logger = logging.getLogger(__name__)


class exercise_title(nodes.strong, nodes.Element):
    """ Title of exercises and solutions """
    pass


class exercise(nodes.Admonition, nodes.Element):
    """ An exercise """
    pass


class solution(nodes.Admonition, nodes.Element):
    """ A solution to an exercice """
    pass


class solutions(nodes.General, nodes.Element):
    """ Set of solutions. The solutions are declared in a exercise
    block, but they can be grouped in the same section. """


class table_of_exercises(nodes.General, nodes.Element):
    """ List of all exercises """
    pass


class SolutionsDirective(SphinxDirective):
    """ Directive replaced with all exercises found in all documents:
        Section number, subsection, exercises...
    """
    def run(self):
        self.env.exercises_all_solutions_docname = self.env.docname
        return [solutions()] # Processed once the toctree is built.


class ExerciseDirective(SphinxDirective):
    """ An exercise """
    final_argument_whitespace = True
    has_content = True
    optional_arguments = 1

    def run(self):
        self.assert_has_content()

        # Destination for a reference to this exercise
        target_id = 'exercise-%d' % self.env.new_serialno('sphinx.ext.exercises')
        target_node = nodes.target('', '', ids=[target_id])

        exercise_node = exercise(self.content, **self.options)

        # Exercise number not known before the toctree is resolved.
        # This title will be modified later.
        exercise_node += nodes.title(_('Exercise'), _('Exercise'))

        # Allow for parsing content as ReST
        self.state.nested_parse(self.content, self.content_offset, exercise_node)

        # Populate exercise pool
        exercise_node['lineno'] = self.lineno
        exercise_node['docname'] = self.env.docname
        exercise_node['title'] = self.arguments[0] if len(self.arguments) else ''
        data = {
            'lineno': self.lineno,
            'docname': self.env.docname,
            'node': exercise_node,
            'title': self.arguments[0] if len(self.arguments) else '',
            'target': target_node,
        }
        self.env.exercises_all_exercises.append(data)
        self.env.exercises_exercises_map[(self.env.docname, target_id)] = data

        return [target_node, exercise_node]


class SolutionDirective(BaseAdmonition):
    node_class = solution

    def run(self):
        if not len(self.arguments):
            self.arguments.append(_('Solution'))

        return super().run()


def env_before_read_docs(app, env, docnames):
    """ Creates the meta data containers. """
    if not hasattr(env, 'exercises_all_exercises'):
        env.exercises_all_exercises = []
    if not hasattr(env, 'exercises_exercises_map'):
        env.exercises_exercises_map = {}


class ExercisesCollector(EnvironmentCollector):
    """ Once the document is parsed, we can identify the chapter numbers
    and add some more information to the exercise pool:
      - Number of exercise (chapter is number[0])
      - Label to display
      - Node with content
    """
    def clear_doc(self, app, env, docname):
        pass

    def process_doc(self, app, doctree):
        pass

    def get_updated_docs(self, app, env):
        """ When a document is updated, the toctree is traversed to
        find new exercises.
        """
        def traverse_all(app, env, docname):
            doctree = env.get_doctree(docname)

            for toc in doctree.traverse(addnodes.toctree):
                for _, subdocname in toc['entries']:
                    traverse_all(app, env, subdocname)

            for node in doctree.traverse(exercise):
                self.process_exercise(app, env, node, docname)

        traverse_all(app, env, env.config.master_doc)

        return []

    def process_exercise(self, app, env, node, docname):
        ids = node['ids']

        # Get exercise node previously created.
        # For some reason attributes cannot be set on the node itself
        solution_nodes = node.traverse(solution)
        number = env.toc_fignumbers.get(docname, {}).get('exercise', {}).get(ids[0])
        env.exercises_exercises_map[(docname, ids[1])].update({
            'number': number,
            'label': app.config.numfig_format['exercise'] % '.'.join(map(str, number)),
            'solution': solution_nodes[0] if len(solution_nodes) == 1 else None
        })


def get_reference(meta):
    return '/'.join(['exercise'] + list(map(str, meta['number'])))


def process_exercise_nodes(app, doctree, fromdocname):
    """ Once the doctree is resolved, the exercices are injected where
    they need to.
    """

    # Sort exercises in ascending order
    all_exercises = app.env.exercises_all_exercises
    all_exercises.sort(key=lambda ex: ex['number'])

    # Regroup exercises organized by chapters
    hierarchy = OrderedDict()
    for ex in all_exercises:
        chapter = ex['number'][0]
        if chapter not in hierarchy:
            hierarchy[chapter] = []
        hierarchy[chapter].append(ex)

    # Populate the solutions directive
    for node in doctree.traverse(solutions):
        content = []
        for chapter, exs in hierarchy.items():
            # Create a section per chapter
            section = nodes.section(ids=[f'solution-chapter-{chapter}'], auto=0)
            name = _('Solutions du chapitre') + ' ' + str(chapter)
            section.append(nodes.title(name, name))
            content.append(section)
            # Insert the solutions
            for ex in [e for e in exs if e['solution']]:
                description = ex['label']
                para = nodes.paragraph()
                para.append(exercise_title(description, description))
                content.append(para)
                content.extend(ex['solution'].children)

        node.replace_self(content)

        # Remove solution from the exercises
        for node in doctree.traverse(exercise):
            node.children = list(filter(lambda x: not isinstance(x, solution), node.children))


def check_config(app, config):
    # Enable numfig, required for this extension
    if not config.numfig:
        logger.error('Numfig config option is disabled, setting it to True')
        config.numfig = True

    config.numfig_format.update({'exercise': _('Exercice %s')}) # TODO: Add translation


def purge(app, env, docname):
    if not hasattr(env, 'exercises_all_exercises'):
        return
    env.exercises_all_exercises = [
        ex for ex in env.exercises_all_exercises
        if ex['docname'] != docname
    ]

def visit_html_exercise(self, node, name=''):
    self.body.append(self.starttag(node, 'div', CLASS=('exercise ' + name)))
    if hasattr(node, 'exnum'): self.body.append('secnum: %s' % str(node.exnum))


def depart_html_exercise(self, node=None):
    self.body.append('</div>\n')


def visit_html_solution(self, node, name=''):
    self.visit_admonition(node, name='solution')


def depart_html_solution(self, node=None):
    self.depart_admonition(node)


def visit_latex_solution(self, node, name=''):
    self.visit_admonition(node, name='solution')


def depart_latex_solution(self, node=None):
    self.depart_admonition(node)


def no_visit(self, node=None):
    pass


def setup(app):
    no_visits = (no_visit, no_visit)

    app.add_enumerable_node(exercise, 'exercise',
        html=(visit_html_exercise, depart_html_exercise),
        latex=no_visits,
        man=no_visits
    )

    app.add_node(solution,
        html=(visit_html_solution, depart_html_solution),
        latex=(visit_latex_solution, depart_latex_solution),
        man=no_visits
    )


    sphinx.locale.admonitionlabels['solution'] = _('Solution')

    app.add_directive('exercise', ExerciseDirective)
    app.add_directive('solution', SolutionDirective)
    app.add_directive('solutions', SolutionsDirective)

    app.connect('config-inited', check_config)
    app.connect('env-before-read-docs', env_before_read_docs)
    app.connect('doctree-resolved', process_exercise_nodes)
    app.connect('env-purge-doc', purge)

    app.add_env_collector(ExercisesCollector)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
