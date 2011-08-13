#!/usr/bin/env python
# -*- Mode: Python -*-
# GObject-Introspection - a framework for introspecting GObject libraries
# Copyright (C) 2010 Zach Goldberg
# Copyright (C) 2011 Johan Dahlin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

import sys

from . import ast
from .girparser import GIRParser
from .xmlwriter import XMLWriter

XMLNS = "http://docbook.org/ns/docbook"
XMLVERSION = "5.0"
DOCTYPE = """<!DOCTYPE refentry PUBLIC "-//OASIS//DTD DocBook XML V4.1.2//EN"
               "http://www.oasis-open.org/docbook/xml/4.1.2/docbookx.dtd" [
<!ENTITY % local.common.attrib "xmlns:xi  CDATA  #FIXED 'http://www.w3.org/2003/XInclude'">
<!ENTITY version SYSTEM "version.xml">
]>"""

def _space(num):
    return " " * num

class DocBookFormatter(object):
    def __init__(self, writer):
        self._namespace = None
        self._writer = writer

    def set_namespace(self, namespace):
        self._namespace = namespace

    def get_type_string(self, type):
        return str(type.ctype)

    def render_parameter(self, param_type, param_name):
        return "%s %s" % (param_type, param_name)

    def _render_parameter(self, param, extra_content=''):
        with self._writer.tagcontext("parameter"):
            if param.type.ctype is not None:
                link_dest = param.type.ctype.replace("*", "")
            else:
                link_dest = param.type.ctype
            with self._writer.tagcontext("link", [("linkend", "%s" % link_dest)]):
                self._writer.write_tag("type", [], link_dest)
            self._writer.write_line(extra_content)

    def _render_parameters(self, parent, parameters):
        self._writer.write_line(
            "%s(" % _space(40 - len(parent.symbol)))

        parent_class = parent.parent_class
        ctype = ast.Type(parent.parent_class.ctype + '*')
        params = []
        params.append(ast.Parameter(parent_class.name.lower(), ctype))
        params.extend(parameters)

        first_param = True
        for param in params:
            if not first_param:
                self._writer.write_line("\n%s" % _space(61))
            else:
                first_param = False

            if not param == params[-1]:
                comma = ", "
            else:
                comma = ""
            extra_content = " "
            if '*' in param.type.ctype:
                extra_content += '*'
            extra_content += param.argname
            extra_content += comma
            self._render_parameter(param, extra_content)

        self._writer.write_line(");\n")

    def get_method_as_title(self, entity):
        method = entity.get_ast()
        return "%s ()" % method.symbol

    def get_page_name(self, node):
        if node.gtype_name is None:
            return node.ctype
        return node.gtype_name

    def get_class_name(self, node):
        if node.gtype_name is None:
            return node.ctype
        return node.gtype_name

    def get_type_name(self, node):
        if isinstance(node, ast.Array):
            if node.array_type == ast.Array.C:
                return str(node.element_type) + "[]"
            else:
                return "%s&lt;%s&gt;" % (node.array_type, str(node.element_type))
        elif isinstance(node, ast.Map):
            return "GHashTable&lt;%s, %s&gt;" % (str(node.key_type), str(node.value_type))
        elif isinstance(node, ast.List):
            return "GList&lt;%s&gt;" % str(node.element_type)
        else:
            return str(node)

    def render_method(self, entity, link=False):
        method = entity.get_ast()
        self._writer.disable_whitespace()

        retval_type = method.retval.type
        if retval_type.ctype:
            link_dest = retval_type.ctype.replace("*", "")
        else:
            link_dest = str(retval_type)

        if retval_type.target_giname:
            ns = retval_type.target_giname.split('.')
            if ns[0] == self._namespace.name:
                link_dest = "%s" % (
                    retval_type.ctype.replace("*", ""))

        with self._writer.tagcontext("link", [("linkend", link_dest)]):
            self._writer.write_tag("returnvalue", [],
                                   self.get_type_string(method.retval.type))

        self._writer.write_line(
            _space(20 - len(self.get_type_string(method.retval.type))))

        if link:
            self._writer.write_tag("link", [("linkend",
                                            "%s-details" % (method.name))],
                                  method.symbol)
        else:
            self._writer.write_line(method.symbol)

        self._render_parameters(method, method.parameters)
        self._writer.enable_whitespace()

    def _get_annotations(self, argument):
        annotations = {}

        if hasattr(argument.type, 'element_type') and \
           argument.type.element_type is not None:
            annotations['element-type'] = argument.type.element_type

        if argument.transfer is not None and argument.transfer != 'none':
            annotations['transfer'] = argument.transfer

        if hasattr(argument, 'allow_none') and argument.allow_none:
            annotations['allow-none'] = None

        return annotations

    def render_param_list(self, entity):
        method = entity.get_ast()

        self._render_param(method.parent_class.name.lower(), 'instance', [])

        for param in method.parameters:
            self._render_param(param.argname, param.doc,
                               self._get_annotations(param))

        self._render_param('Returns', method.retval.doc,
                           self._get_annotations(method.retval))

    def _render_param(self, argname, doc, annotations):
        with self._writer.tagcontext('varlistentry'):
            with self._writer.tagcontext('term'):
                self._writer.disable_whitespace()
                try:
                    with self._writer.tagcontext('parameter'):
                        self._writer.write_line(argname)
                    if doc is not None:
                        self._writer.write_line('&#xA0;:')
                finally:
                    self._writer.enable_whitespace()
            if doc is not None:
                with self._writer.tagcontext('listitem'):
                    with self._writer.tagcontext('simpara'):
                        self._writer.write_line(doc)
                        if annotations:
                            with self._writer.tagcontext('emphasis', [('role', 'annotation')]):
                                for key, value in annotations.iteritems():
                                    self._writer.disable_whitespace()
                                    try:
                                        self._writer.write_line('[%s' % key)
                                        if value is not None:
                                            self._writer.write_line(' %s' % value)
                                        self._writer.write_line(']')
                                    finally:
                                        self._writer.enable_whitespace()

    def render_property(self, entity, link=False):
        prop = entity.get_ast()

        prop_name = '"%s"' % prop.name
        prop_type = self.get_type_name(prop.type)

        flags = []
        if prop.readable:
            flags.append("Read")
        if prop.writable:
            flags.append("Write")
        if prop.construct:
            flags.append("Construct")
        if prop.construct_only:
            flags.append("Construct Only")

        self._render_prop_or_signal(prop_name, prop_type, flags)

    def _render_prop_or_signal(self, name, type_, flags):
        self._writer.disable_whitespace()

        line = _space(2) + name + _space(27 - len(name))
        line += str(type_) + _space(22 - len(str(type_)))
        line += ": " + " / ".join(flags)

        self._writer.write_line(line + "\n")

        self._writer.enable_whitespace()


    def render_signal(self, entity, link=False):
        signal = entity.get_ast()

        sig_name = '"%s"' % signal.name
        flags = ["TODO: signal flags not in GIR currently"]
        self._render_prop_or_signal(sig_name, "", flags)


class DocBookPage(object):
    def __init__(self, name, ast):
        self.methods = []
        self.properties = []
        self.signals = []
        self.name = name
        self.description = ast.doc
        self.ast = ast
        self.id = None

    def add_method(self, entity):
        self.methods.append(entity)

    def add_property(self, entity):
        self.properties.append(entity)

    def add_signal(self, entity):
        self.signals.append(entity)

    def get_methods(self):
        return self.methods

    def get_properties(self):
        return self.properties

    def get_signals(self):
        return self.signals

class DocBookEntity(object):
    def __init__(self, entity_name, entity_type, entity_ast):
        self.entity_name = entity_name
        self.entity_type = entity_type
        self.entity_ast = entity_ast

    def get_ast(self):
        return self.entity_ast

    def get_type(self):
        return self.entity_type

    def get_name(self):
        return self.entity_name


class DocBookWriter(object):
    def __init__(self):
        self._namespace = None
        self._pages = []

        self._writer = XMLWriter()
        self._formatter = DocBookFormatter(self._writer)

    def _add_page(self, page):
        self._pages.append(page)

    def add_transformer(self, transformer):
        self._transformer = transformer

        self._namespace = self._transformer._namespace
        self._formatter.set_namespace(self._namespace)

        for name, node in self._namespace.iteritems():
            if isinstance(node, (ast.Class, ast.Record, ast.Interface)):
                page_name = self._formatter.get_page_name(node)
                self._add_node(node, page_name)

    def _add_node(self, node, name):
        page = DocBookPage(name, node)
        self._add_page(page)

        if isinstance(node, (ast.Class, ast.Record, ast.Interface)):
            page.id = node.ctype
            for method in node.methods:
                method.parent_class = node
                page.add_method(DocBookEntity(method.name, "method", method))

        if isinstance(node, (ast.Class, ast.Interface)):
            for property_ in node.properties:
                page.add_property(DocBookEntity(property_.name, "property", property_))
            for signal in node.signals:
                page.add_signal(DocBookEntity(signal.name, "signal", signal))

    def write(self, output):
        self._writer.write_line(DOCTYPE)
        with self._writer.tagcontext("book", [
            ("xml:id", "page_%s" % self._namespace.name),
            ("xmlns", XMLNS),
            ("version", XMLVERSION)]):
            self._writer.write_tag("title", [], "%s Documentation" % (
                self._namespace.name))

            for page in self._pages:
                self._render_page(page)

        fp = open(output, 'w')
        fp.write(self._writer.get_xml())
        fp.close()

    def _render_page(self, page):
        with self._writer.tagcontext("chapter", [("xml:id", "ch_%s" % (
                        page.name))]):
            self._writer.write_tag(
                "refentry", [("id", "%s" % (page.id))])
            self._writer.write_tag(
                "title", [], page.name)

            with self._writer.tagcontext("refsynopsisdiv",
                    [('id', '%s.synopsis' % page.name),
                     ('role', 'synopsis')]):
                self._writer.write_tag(
                    "title", [("role", "synopsis.title")], "Synopsis")
                with self._writer.tagcontext('synopsis'):
                    for entity in page.get_methods():
                        self._formatter.render_method(entity, link=True)

            if isinstance(page.ast, (ast.Class, ast.Interface)):
                with self._writer.tagcontext("refsect1",
                                            [('id', '%s.object-hierarchy' % page.name),
                                             ('role', 'object_hierarchy')]):
                    self._writer.write_tag('title', [('role', 'object_hierarchy.title')],
                                          "Object Hierarchy")
                    with self._writer.tagcontext('synopsis'):
                        self._render_page_object_hierarchy(page.ast)

            if page.get_properties():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.properties' % page.name),
                                             ('role', 'properties')]):
                    self._writer.write_tag("title", [('role', 'properties.title')],
                                          "Properties")
                    with self._writer.tagcontext("synopsis"):
                        for entity in page.get_properties():
                            self._formatter.render_property(entity, link=True)

            if page.get_signals():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.signals' % page.name),
                                             ('role', 'signal_proto')]):
                    self._writer.write_tag('title', [('role', 'signal_proto.title')],
                                          "Signals")
                    with self._writer.tagcontext('synopsis'):
                        for entity in page.get_signals():
                            self._formatter.render_signal(entity, link=True)

            # if page.description:
            #     with self._writer.tagcontext(
            #         'refsect1',
            #         [('id', '%s.description' % (page.name, )),
            #          ]):
            #         self._writer.write_tag(
            #             "title", [("role", "desc.title")], "Description")
            #         import cgi
            #         desc = page.description
            #         while True:
            #             start = desc.find('|[')
            #             if start == -1:
            #                 break
            #             end = desc.find(']|')
            #             desc = desc[:start] + cgi.escape(desc[start+2:end]) + desc[end+2:]
            #         desc = desc.replace("&", "&amp;")
            #         self._writer.write_line(desc)

            if page.get_methods():
                with self._writer.tagcontext('refsect1',
                                            [('id', "%s-details" % page.name),
                                             ("role", "details")]):
                    self._writer.write_tag("title", [("role", "details.title")],
                                          "Details")
                    for entity in page.get_methods():
                        self._render_method(entity)

            if page.get_properties():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.property-details' % page.name),
                                             ('role', 'property_details')]):
                    self._writer.write_tag('title', [('role', 'property_details.title')],
                                           "Property Details")
                    for entity in page.get_properties():
                        self._render_property(entity)

            if page.get_signals():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.signal-details' % page.name),
                                             ('role', 'signals')]):
                    self._writer.write_tag('title', [('role', 'signal.title')],
                                           "Signal Details")
                    for entity in page.get_signals():
                        self._render_signal(entity)

    def _render_method(self, entity):

        self._writer.push_tag('refsect2',
                             [('id', entity.get_ast().symbol),
                              ('role', 'struct')])
        self._writer.write_tag("title", [],
                               self._formatter.get_method_as_title(entity))

        with self._writer.tagcontext("indexterm",
                                    [("zone", "%s" % entity.get_name())]):
            self._writer.write_tag("primary", [], entity.get_name())

        with self._writer.tagcontext("programlisting"):
            self._formatter.render_method(entity)

        self._writer.write_tag("para", [], entity.get_ast().doc)

        with self._writer.tagcontext("variablelist", [("role", "params")]):
            self._formatter.render_param_list(entity)

        self._writer.pop_tag()

    def _render_property(self, entity):
        self._writer.write_line("Not implemented yet")

    def _render_signal(self, entity):
        self._writer.write_line("Not implemented yet")

    def _render_page_object_hierarchy(self, page_node):
        parent_chain = self._get_parent_chain(page_node)
        parent_chain.append(page_node)
        lines = []

        for level, parent in enumerate(parent_chain):
            prepend = ""
            if level > 0:
                prepend = _space((level - 1)* 6) + " +----"
            lines.append(_space(2) + prepend + self._formatter.get_class_name(parent))

        self._writer.disable_whitespace()
        self._writer.write_line("\n".join(lines))
        self._writer.enable_whitespace()

    def _get_parent_chain(self, page_node):
        parent_chain = []

        node = page_node
        while node.parent:
            node = self._transformer.lookup_giname(str(node.parent))
            parent_chain.append(node)

        parent_chain.reverse()
        return parent_chain
