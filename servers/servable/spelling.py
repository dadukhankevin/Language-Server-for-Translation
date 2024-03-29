from tools.spell_check import Dictionary, SpellCheck
from tools.ls_tools import ServerFunctions
from lsprotocol.types import (DocumentDiagnosticParams, CompletionParams, 
    CodeActionParams, Range, CompletionItem, CompletionItemKind, 
    TextEdit, Position, Diagnostic, DidCloseTextDocumentParams, CodeAction, WorkspaceEdit, CodeActionKind, Command, DiagnosticSeverity)

from pygls.server import LanguageServer
from typing import List
import re

def is_bible_ref(text):
    pattern = r'\b\d*\s*[A-Z]+\s\d+:\d+\b'
    match = re.search(pattern, text)
    
    return bool(match)

class ServableSpelling:
    def __init__(self, sf: ServerFunctions, relative_checking=False):
        self.dictionary = None 
        self.spell_check = None
        self.relative_checking = relative_checking
        self.sf = sf
        self.sf.initialize_functions.append(self.initialize)

    def spell_completion(self, server: LanguageServer, params: CompletionParams, range: Range, sf: ServerFunctions) -> List:
        try:
            document_uri = params.text_document.uri
            document = server.workspace.get_document(document_uri)
            line = document.lines[params.position.line]
            word = line.strip().split(" ")[-1]
            completions = self.spell_check.complete(word=word)
            return [CompletionItem(
                label=word+completion,
                text_edit=TextEdit(range=range, new_text=completion),
                ) for completion in completions]
        except IndexError:
            return []

    def spell_diagnostic(self, ls, params: DocumentDiagnosticParams, sf: ServerFunctions):
        diagnostics = []
        document_uri = params.text_document.uri
        if ".codex" in document_uri or ".scripture" in document_uri:
            document = ls.workspace.get_document(document_uri)
        lines = document.lines
        for line_num, line in enumerate(lines):
            if is_bible_ref(line):
                continue
            
            words = line.split(" ")
            edit_window = 0

            for word in words:
                check = self.spell_check.is_correction_needed(word)
                if check:
                    start_char = edit_window
                    end_char = start_char + len(word)
                    
                    range = Range(start=Position(line=line_num, character=start_char),
                                end=Position(line=line_num, character=end_char))
                    diagnostics.append(Diagnostic(range=range, message='Potential Typo', severity=DiagnosticSeverity.Warning, source='Spell-Check'))
                
                # Update edit_window based on cumulative character count
                edit_window += len(word) + 1  # +1 for the space between words

        return diagnostics 
    
    def spell_action(self, ls: LanguageServer, params: CodeActionParams, range: Range, sf: ServerFunctions) -> List[CodeAction]:
        document_uri = params.text_document.uri
        document = ls.workspace.get_document(document_uri)
        diagnostics = params.context.diagnostics
        
        actions = []
        typo_diagnostics = []
        start_line = None
        for diagnostic in diagnostics:
            if diagnostic.message == "Potential Typo":
                typo_diagnostics.append(diagnostic)
                start_line = diagnostic.range.start.line
                start_character = diagnostic.range.start.character
                end_character = diagnostic.range.end.character
                word = document.lines[start_line][start_character:end_character]
                try:
                    corrections = self.spell_check.check(word)
                except IndexError:
                    corrections = []
                if is_bible_ref(document.lines[start_line]):
                    return []
                for correction in corrections:
                    edit = TextEdit(range=diagnostic.range, new_text=correction)
                    
                    action = CodeAction(
                        title=f"Change '{word}' to '{correction}'",
                        kind=CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                        edit=WorkspaceEdit(changes={document_uri: [edit]}))
                    
                    actions.append(action)

                add_word_action = CodeAction(
                    title=f"Add '{word}' to dictionary",
                    kind=CodeActionKind.QuickFix,
                    diagnostics=[diagnostic],
                    command=Command('Add to Dictionary', command='pygls.server.add_dictionary', arguments=[[word]])
                )
                actions.append(add_word_action)
                add_word_action = CodeAction(
                            title=f"Add all to dictionary",
                            kind=CodeActionKind.QuickFix,
                            diagnostics=[diagnostic],
                            command=Command('Add to Dictionary', command='pygls.server.add_dictionary', arguments=[document.lines[start_line].split(" ")])
                        )
                actions.append(add_word_action)
            
        return actions
    
    def add_dictionary(self, args):
        args = args[0]
        for word in args:
            self.dictionary.define(word, level='verified')
        self.sf.server.show_message("Dictionary updated.")

    def initialize(self, params, server: LanguageServer, sf):
        self.dictionary = Dictionary(self.sf.data_path)
        self.spell_check = SpellCheck(dictionary=self.dictionary, relative_checking=self.relative_checking)