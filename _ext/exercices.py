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

logger = logging.getLogger(__name__)


class exercise(nodes.Admonition, nodes.Element):
    pass


class solution(nodes.Admonition, nodes.Element):
    pass


class all_exercises(nodes.General, nodes.Element):
    pass

class all_solutions(nodes.General, nodes.Element):
    pass


class AllExercisesDirective(SphinxDirective):
    """ Directive replaced with all exercises found in all documents:
        Section number, subsection, exercises...
    """
    def run(self):
        self.env.exercises_all_exercises_docname = self.env.docname
        return [all_exercises()] # Let it process later once the toctree is built

class AllSolutionsDirective(SphinxDirective):
    """ Directive replaced with all exercises found in all documents:
        Section number, subsection, exercises...
    """
    def run(self):
        self.env.exercises_all_exercises_docname = self.env.docname
        return [all_solutions()] # Let it process later once the toctree is built


class ExerciseDirective(SphinxDirective):
    final_argument_whitespace = True
    has_content = True
    optional_arguments = 1

    def run(self):
        self.assert_has_content()

        id = 'exercise-%d' % self.env.new_serialno('sphinx.ext.exercises#exercises')
        logger.debug(f"[exercises] New id for exercise {id}")

        target_node = nodes.target('', '', ids=[id])

        node = exercise(self.content, **self.options)
        node += nodes.title() # Populated lated
        self.state.nested_parse(self.content, self.content_offset, node)

        self.env.exercises_all_exercises[(self.env.docname, id)] = {
            'lineno': self.lineno,
            'docname': self.env.docname,
            'node': node,
            'title': self.arguments[0] if len(self.arguments) else '',
            'target': target_node,
        }

        return [target_node, node]

class SolutionDirective(BaseAdmonition):
    node_class = solution

    def run(self):
        if not len(self.arguments):
            self.arguments.append(_('Solution'))

        return super().run()

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


def get_reference(meta):
    return '/'.join(['exercise'] + list(map(str, meta['number'])))


def process_exercise_nodes(app, doctree, fromdocname):
    """ Once the doctree is resolved, the exercices are injected where
    they need to.
    """
    for node in doctree.traverse(exercise):
        """
        Replace each exercises with a link
        """
        para = nodes.paragraph()

        if (fromdocname, node['ids'][1]) not in app.env.exercises_all_exercises:
            continue

        meta = app.env.exercises_all_exercises[(fromdocname, node['ids'][1])]
        description = meta['label']

        ref = nodes.reference('','')
        innernode = nodes.Text(description, description)
        ref['refdocname'] = fromdocname

        if hasattr(app.env, 'exercises_all_exercises_docname'):
            ref['refuri'] = app.builder.get_relative_uri(fromdocname, app.env.exercises_all_exercises_docname)
            ref['refuri'] += '#' + get_reference(meta)

        ref.append(innernode)
        para += ref
        para += nodes.Text(': ' + meta['title'], ': ' + meta['title'])

        #node.parent.replace(node, para)

    for node in doctree.traverse(all_exercises):
        content = []

        chapter = -1

        titles = { value[''][0]: app.env.titles[key].astext()
            for key, value in app.env.toc_secnumbers.items()
        }

        all_exs = sorted(app.env.exercises_all_exercises.items(), key=lambda x: x[1]['number'])

        def cat2exercise(cat):
            ex = cat[1]
            return ex['label'] + ' ' + ex['title']

        for _, ex in status_iterator(all_exs, 'collecting exercises... ', "darkgreen",
            len(all_exs), stringify_func=cat2exercise):
            n = ex['node']

            if ex['number'][0] != chapter:
                chapter = ex['number'][0]
                title = nodes.title('','%d. %s' % (chapter, titles[chapter]))
                content.append(title)

            title = nodes.caption('', ex['label'] + ' ' + ex['title'])

            n.replace(n.children[n.first_child_matching_class(nodes.title)], title )
            n['ids'] = [get_reference(ex)]

            content.append(n)

        node.replace_self(content)

    # Build list of solutions
    chapters = OrderedDict()
    for _, ex in sorted(app.env.exercises_all_exercises.items(), key=lambda x: x[1]['number']):
        if ex['solution']:
            chapter = ex['number'][0]
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(ex)

    for node in doctree.traverse(all_solutions):
        content = []
        for num, chapter in sorted(chapters.items(), key=lambda x: x[0]):
            id = 'solution-title-%d' % app.env.new_serialno('sphinx.ext.exercises#solutions')
            section = nodes.section(ids=[id], auto=0)
            name = f'Exercices du chapitre {num}'
            section.append(nodes.title(text=name))
            content.append(section)

            for ex in chapter:
                description = ex['label']
                para = nodes.paragraph()
                innernode = nodes.strong(description, description)
                para.append(innernode)
                content.append(para)
                content.extend(ex['solution'].children)
        node.replace_self(content)


    for node in doctree.traverse(exercise):
        # Remove solution from question
        node.children = list(filter(lambda x: not isinstance(x, solution), node.children))

class ExercisesCollector(EnvironmentCollector):
    """ Add information to the exercises pool:
      - Number of exercise (chapter is number[0])
      - Label to display
      - Node with content
    """
    def clear_doc(self, app, env, docname):
        pass

    def process_doc(self, app, doctree):
        pass

    def get_updated_docs(self, app, env):
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
        meta = env.exercises_all_exercises[(docname, node['ids'][1])]
        meta['number'] = env.toc_fignumbers.get(docname, {}).get('exercise', {}).get(node['ids'][0])
        meta['label'] = app.config.numfig_format['exercise'] % '.'.join(map(str, meta['number']))
        sol = node.traverse(solution)
        meta['solution'] = None
        if len(sol) == 1:
            meta['solution'] = sol[0]

        env.all_exercises.append(meta)

def check_config(app, config):
    # Enable numfig, required for this extension
    if not config.numfig:
        logger.error('Numfig config option is disabled, setting it to True')
        config.numfig = True

    config.numfig_format.update({'exercise': _('Exercice %s')}) # TODO: Add translation

def env_before_read_docs(app, env, docnames):
    if not hasattr(env, 'all_exercises'):
        env.all_exercises = []
    if not hasattr(env, 'exercises_all_exercises'):
        env.exercises_all_exercises = OrderedDict()

class PostTransform(SphinxTransform):
    """
    update source and rawsource attributes
    """
    default_priority = 900

    def apply(self, **kwargs):
        for node in self.document.traverse(solution):
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
    app.add_directive('exercises', AllExercisesDirective)
    app.add_directive('solutions', AllSolutionsDirective)

    app.connect('config-inited', check_config)
    app.connect('env-before-read-docs', env_before_read_docs)
    app.connect('doctree-resolved', process_exercise_nodes)

    app.add_transform(PostTransform)
    app.add_env_collector(ExercisesCollector)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
