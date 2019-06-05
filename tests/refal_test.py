#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

import pytest

from refal.refalcheck import *


@pytest.fixture
def built_in_parser():
    file_type_path = join(dirname(dirname(__file__)), 'refal', 'built-in.type').replace("\\", "/")
    parser_refal_type = calculate_ast(file_type_path, True)

    return parser_refal_type


def file_parser(name_file, is_file_type=False):
    file_refal_path = join(dirname(__file__), 'files', name_file).replace("\\", "/")
    parser_refal = calculate_ast(file_refal_path, is_file_type)

    return parser_refal


def run_easy_test(name_file, built_in_parser, contain_file_type=False):
    parser_refal = file_parser(name_file)
    parser_refal_type = built_in_parser

    if contain_file_type:
        append_ast(parser_refal_type, calculate_ast(join(dirname(__file__), 'files', name_file).replace("\\", "/").
                                                    replace(".ref", ".type"), True))

    parser_refal.semantics_call(parser_refal_type.ast)

    assert not parser_refal.isError
    assert not parser_refal_type.isError

    if not parser_refal.isError and not parser_refal_type.isError:
        calculation = Calculation(parser_refal.ast, parser_refal_type.ast)
        calculation.calculate_system()
        output = calculation.print_format_function()

        output_format = [line for line in output.split("\n") if line and line != '/* result program refalcheck */']

        return output_format


@pytest.mark.timeout(1)
def test_1(built_in_parser):
    output_format = run_easy_test("test1.ref", built_in_parser)

    assert output_format[0] == "*Trans-line e = e"
    assert output_format[1] == "*Table  = (('cane') 'dog') (('gatto') 'cat') (('cavallo') 'horse') (('rana') " \
                               "'frog') (('porco') 'pig')"
    assert output_format[2] == "*Trans (e) e = e"


@pytest.mark.timeout(1)
def test_3(built_in_parser):
    output_format = run_easy_test("test3.ref", built_in_parser)

    assert output_format[0] == "*F s e = s"


@pytest.mark.timeout(10)
def test_4(built_in_parser):
    output_format = run_easy_test("test4.ref", built_in_parser)

    assert output_format[0] == "Go  = "
    assert output_format[1] == "*CheckArg e = "
    assert output_format[2] == "*ReadLines e = e"
    assert output_format[3] == "*Format e = '<html><body>\\n<h1>Оглавление</h1>\\n' e '</body></html>'"
    assert output_format[4] == "*Trim-Left e = e"
    assert output_format[5] == "*FormatRec s e = e"
    assert output_format[6] == "*AddTableContent s e = e"


@pytest.mark.timeout(1)
def test_5(built_in_parser):
    output_format = run_easy_test("test5.ref", built_in_parser)

    assert output_format[0] == "Go  = "
    assert output_format[1] == "*CheckArg e = "
    assert output_format[2] == "*ReadLines e = e"
    assert output_format[3] == "*Format e = '<html><body>\\n' e '</body></html>'"
    assert output_format[4] == "*Trim-Left e = e"
    assert output_format[5] == "*FormatRec e = e"
    assert output_format[6] == "*CodeBlock e = e"
    assert output_format[7] == "*DeleteCodeBlock e = e"
    assert output_format[8] == "*Fix e = e"


@pytest.mark.timeout(60)
def ttest_6(built_in_parser):
    output_format = run_easy_test("test6.ref", built_in_parser)

    assert output_format[0] == "Go  = "
    assert output_format[1] == "*CheckArg e = "
    assert output_format[2] == "*CountWords s e = "
    assert output_format[3] == "*CountWordsRec s e = "
    assert output_format[4] == "*Trim-Left e = e"
    assert output_format[5] == "*DoCountWordsFile (s) e = e"
    assert output_format[6] == "*DoCountWordsInput (s) e = e"


@pytest.mark.timeout(1)
def test_7(built_in_parser):
    output_format = run_easy_test("test7.ref", built_in_parser)

    assert output_format[0] == "Go  = "
    assert output_format[1] == "*ReadInput e = e"
    assert output_format[2] == "*CheckNumber s (e) = s s s s e '\\n'"


@pytest.mark.timeout(1)
def test_8(built_in_parser):
    output_format = run_easy_test("test8.ref", built_in_parser)

    assert output_format[0] == "*DoHexDigit s e s = e"


@pytest.mark.timeout(1)
def test_10(built_in_parser):
    output_format = run_easy_test("test10.ref", built_in_parser)

    assert output_format[0] == "*F s e (e) = s e"
    assert output_format[1] == "*G s e = s"
    assert output_format[2] == "*H e (e) = e"


@pytest.mark.timeout(1)
def test_11(built_in_parser):
    output_format = run_easy_test("test11.ref", built_in_parser)

    assert output_format[0] == "*Job e = e"
    assert output_format[1] == "*Trans (e) e = e"
    assert output_format[2] == "*Fact s = s e"
    assert output_format[3] == "*Table  = (('cane') 'dog') (('gatto') 'cat') (('cavallo') 'horse') (('rana') 'frog') " \
                               "(('porco') 'pig')"
    assert output_format[4] == "*Trans-line e = e"


@pytest.mark.timeout(1)
def test_12(built_in_parser):
    output_format = run_easy_test("test12.ref", built_in_parser)

    assert output_format[0] == "*F @ = @"


@pytest.mark.timeout(1)
def test_13(built_in_parser):
    output_format = run_easy_test("test13.ref", built_in_parser)

    assert output_format[0] == "*Fab (e) e = e"


@pytest.mark.timeout(1)
def test_14(built_in_parser):
    output_format = run_easy_test("test14.ref", built_in_parser, True)

    assert output_format[0] == "*F A e = A"


@pytest.mark.timeout(1)
def test_15(built_in_parser, capsys):
    _ = run_easy_test("test15.ref", built_in_parser)

    captured = capsys.readouterr()
    output = re.sub(r'\.[\d]+', '', captured.err)
    assert output == "Function F, sentence 0, there isn't solution for equation: A A e : in[F] => A\n"


def ttest_17(built_in_parser):
    output_format = run_easy_test("test17.ref", built_in_parser)

    assert output_format[0] == "Apply t e = e"
    assert output_format[1] == "Map t e = e"
    assert output_format[2] == "Reduce t t e = t"
    assert output_format[3] == "MapAccum t t e = t e"
    assert output_format[4] == "*DoMapAccum t t (e) e = t e"
    assert output_format[5] == "*MapAccum-AddScanned t e (e) = t (e)"
    assert output_format[6] == "DelAccumulator t e = e"
    assert output_format[7] == "*LOAD-SAVE-HANDLE  = 39"
    assert output_format[8] == "LoadFile e = e"
    assert output_format[9] == "*DoLoadFile e = e"
    assert output_format[10] == "SaveFile (e) e = e"
    assert output_format[11] == "*SaveFile-WriteBracketLine (e) = "
    assert output_format[12] == "Inc s = s e"
    assert output_format[13] == "Dec s = s e"
    assert output_format[14] == "ArgList  = e"
    assert output_format[15] == "*DoArgList s = e"
    assert output_format[16] == "*SwDoArgList s e = e"
    assert output_format[17] == "Trim e = e"
    assert output_format[18] == "*Trim-R e = e"


@pytest.mark.timeout(1)
def test_18(built_in_parser):
    output_format = run_easy_test("test18.ref", built_in_parser, True)

    assert output_format[0] == "generator_GenSentence t = () ('  ' s s s s e) e"
    assert output_format[1] == "*SkipIndentAccum ('    ') e = e"
    assert output_format[2] == "*CompileSentence (e) (e) = e"


@pytest.mark.timeout(1)
def test_19(built_in_parser):
    output_format = run_easy_test("test19.ref", built_in_parser)

    assert output_format[0] == "refal05c_WriteError e ((s s) e) = "
    assert output_format[1] == "*StrFromSrcPos (s s) = e"


@pytest.mark.timeout(1)
def test_20(built_in_parser):
    output_format = run_easy_test("test20.ref", built_in_parser, True)

    assert output_format[0] == "refal05c_ProcessEachSource (s e) = e t"
    assert output_format[1] == "*CompileSource-SwSuccessedParse (e) (e) s e = e t"


def te_21(built_in_parser):
    output_format = run_easy_test("test21.ref", built_in_parser, True)

    assert output_format[0] == "R05-Generate-ToFile (e) e = "
    assert output_format[1] == "R05-Generate-ToLines e = e"
    assert output_format[2] == "Generate (e) e = e"
    assert output_format[3] == "R05-Generate-Aux (e) (e) e = e"
    assert output_format[4] == "generator_GenTreeItem (e) (s e) = (e) e"
    assert output_format[5] == "TextFromScopeClass s = e"
    assert output_format[6] == "GenDeclaration s e = (s s s s s s ' struct r05_function r05f_' e ';')"
    assert output_format[7] == "GenFunction s (e) s e = (e s s s s) (e) e"
    assert output_format[8] == "GenFunctionBody s e = (s e s) e"
    assert output_format[9] == "AddFailCommand e = e t"
    assert output_format[10] == "generator_GenSentence t = () ('  ' s s s s e) e"
    assert output_format[11] == "SkipIndentAccum ('    ') e = e"
    assert output_format[12] == "RangeVar-B s = 'bb[' e ']'"
    assert output_format[13] == "RangeVar-E s = 'be[' e ']'"
    assert output_format[14] == "RangeVarsPtr s = 'bb+' e"
    assert output_format[15] == "SafeComment e = e"
    assert output_format[16] == "generator_GenCommand (e) (s e) = (e) e"
    assert output_format[17] == "CmdComment (e) e = (e ' */')"
    assert output_format[18] == "CmdDeclareVar (e) s s e = (e ';') e"
    assert output_format[19] == "CmdRangeArray (e) s = (e '] = { 0 };') (e '] = { 0 };')"
    assert output_format[20] == "CmdInitB0 (e) = (e ', arg_begin, arg_end);')"
    assert output_format[21] == "CmdMatch (e) s s s e = (e '))') (e '  continue;')"
    assert output_format[22] == "MatchFunc s s e = s s s s e"
    assert output_format[23] == "SymbolFunc s = s s s s e"
    assert output_format[24] == "StrFromDirection s = s s s e 't'"
    assert output_format[25] == "MatchArgs s s e = e"
    assert output_format[26] == "SymbolTextRep s t e = e"
    assert output_format[27] == "CmdEmpty (e) s = (e ']))') (e '  continue;')"
    assert output_format[28] == "CmdClosedE (e) s 'e' e = (e '];') (e '];')"
    assert output_format[29] == "CmdOpenedE-Start (e) s 'e' e = (e ' = 0;') (e ' = 0;') (e 'r05_start_e_loop();') (e " \
                                "'do {')"
    assert output_format[30] == "CmdOpenedE-End (e) s 'e' e = (e '));') (e 'r05_stop_e_loop();')"
    assert output_format[31] == "CmdSave (e) s s = (e '];') (e '];')"
    assert output_format[32] == "CmdEmptyResult (e) = () (e 'r05_reset_allocator();')"
    assert output_format[33] == "CmdResultArray (e) s = (e '] = { 0 };')"
    assert output_format[34] == "CmdAllocateElem (e) s e = (e)"
    assert output_format[35] == "ElSymbol s t e = s s s s e ');'"
    assert output_format[36] == "ElString s e = 'chars(\"' e ');'"
    assert output_format[37] == "ElOpenBracket s = 'open_bracket(n+' e ');'"
    assert output_format[38] == "ElCloseBracket s = 'close_bracket(n+' e ');'"
    assert output_format[39] == "ElOpenCall s = 'open_call(n+' e ');'"
    assert output_format[40] == "ElCloseCall s = 'close_call(n+' e ');'"
    assert output_format[41] == "ElSavePos s = 'insert_pos(n+' e ');'"
    assert output_format[42] == "ElVariable s e = s 'var(' s e ');'"
    assert output_format[43] == "CmdLinkBrackets (e) s s = (e ']);')"
    assert output_format[44] == "CmdPushStack (e) s = (e ']);')"
    assert output_format[45] == "CmdInsertVar (e) s s s e = (e ');')"
    assert output_format[46] == "CmdReturnResult (e) = (e 'r05_splice_from_freelist(arg_begin);') (e " \
                                "'r05_splice_to_freelist(arg_begin, arg_end);') (e 'return;')"
    assert output_format[47] == "EscapeString e = e"
    assert output_format[48] == "EscapeChar s = s e"
    assert output_format[49] == "EscapeChar-Aux s s = s e"
    assert output_format[50] == "EscapeChar-SwCompare s s s s = s e"
    assert output_format[51] == "Var s s e = s e"
    assert output_format[52] == "VarPtr s s e = '&' s e"
    assert output_format[53] == "EVar-B s 'e' e = 'e' e"
    assert output_format[54] == "EVar-E s 'e' e = 'e' e"
    assert output_format[55] == "Elem s = 'n[' e ']'"
    assert output_format[56] == "ElemPtr s = 'n+' e"
    assert output_format[57] == "GenNative (e s) e = (BeginNative e s) e (EndNative)"
    assert output_format[58] == "GenPostprocess (e) e = e"
    assert output_format[59] == "generator_EnumerateLines (e) s (e) = s (e)"
    assert output_format[60] == "LineDirective s e = ('#line ' e '\"')"
    assert output_format[61] == "CompileSentence (e) (e) = e"
    assert output_format[62] == "CompileSentence-Aux s (e) (e) e = e"
    assert output_format[63] == "GenPattern e = s (e) (e)"
    assert output_format[64] == "DoGenPattern s e (e) (e) = s (e) (e)"
    assert output_format[65] == "SaveRanges s (e) (e) (e) e = s e (e) (e)"
    assert output_format[66] == "GenResult (e) e = s (e) (e)"
    assert output_format[67] == "DecUsings s s e = e"
    assert output_format[68] == "ComposeSentenceCommands s (e) (e) s (e) (e) = e"
    assert output_format[69] == "FilterCommonVarsAndPatternCommands (e) (e) e = (e) e"
    assert output_format[70] == "ComposeSentenceCommands-Aux s s (e) (e) e = e"
    assert output_format[71] == "generator_MakeDeclaration (s s e) = (CmdDeclareVar s s e) e"
    assert output_format[72] == "MakeDeclaration-Aux s s e = e"
    assert output_format[73] == "MakeCmdResultCommand s = e"
    assert output_format[74] == "GenerateResult-OpenELoops e = e"


def ttest_22(built_in_parser):
    output_format = run_easy_test("test22.ref", built_in_parser, True)

    assert output_format[0] == "R05-Parse-File e = s e"
    assert output_format[1] == "R05-Parse-String e = s e"
    assert output_format[2] == "R05-Parse-Tokens e = s e"
    assert output_format[3] == "R05-Parse-Aux t e = s e"
    assert output_format[4] == "R05-Parse-SwErrors (e) e = s e"
    assert output_format[5] == "SortErrors e = e"
    assert output_format[6] == "DoSortErrors (e) e = e"
    assert output_format[7] == "SortErrors-Insert e t = e t"
    assert output_format[8] == "SortErrors-Insert-Compare e t t s = e t t"
    assert output_format[9] == "CompareError ((s s) e) ((s s) e) = s"
    assert output_format[10] == "ParseProgram e t = t (e) e"
    assert output_format[11] == "ParseElement (s t e) e t = e t"
    assert output_format[12] == "parser_MakeListFunction s (t e) = (Function t s (e) Sentences)"
    assert output_format[13] == "ParseList (s t e) e t = (s t e) e (ErrorList e)"
    assert output_format[14] == "ParseListKeyWord (s t e) e t = (ListKeyWord s) e t"
    assert output_format[15] == "ParseFunction e t = t e t"
    assert output_format[16] == "ParseScope e t = (Scope s) e t"
    assert output_format[17] == "ParseBody e t = (Body (e) s e) e t"
    assert output_format[18] == "ParseSentences e t = (Sentences (e) e) (TkCloseBlock t) e t"
    assert output_format[19] == "ParseSentence e t = (Sentence (e) (e) (e)) e t"
    assert output_format[20] == "ParsePattern s e t = (Pattern (e) (e) e) e t"
    assert output_format[21] == "CleanupDoubleVars e (e) = e"
    assert output_format[22] == "ParsePatternTerm e t = (s e) e t"
    assert output_format[23] == "ParseResult s e (e) t = (Result (e) e) e t"
    assert output_format[24] == "ParseResultTerm e (e) t = (s e) e (e) t"
    assert output_format[25] == "BracketPairName s = s"
    assert output_format[26] == "SemanticCheck t (e) e = t e"
    assert output_format[27] == "FindOneEntry t (e) e = t e"
    assert output_format[28] == "LoadBuiltins  = e"
    assert output_format[29] == "parser_BuiltinDeclaration (s s s) = e"
    assert output_format[30] == "Normalize e = e"
    assert output_format[31] == "CheckRepeatedDefinitions t e (e) = t e"
    assert output_format[32] == "RemoveReference (e) e = e"
    assert output_format[33] == "parser_AddUnresolved (ErrorList e) (t e) = (ErrorList e (t e))"
    assert output_format[34] == "EL-Create  = (ErrorList)"
    assert output_format[35] == "EL-AddErrorAt (ErrorList e) t e = (ErrorList e (t e))"
    assert output_format[36] == "EL-AddUnexpected t (s t e) e = (ErrorList e (t e))"
    assert output_format[37] == "EL-Destroy (ErrorList e) = e"


def ttest_23(built_in_parser):
    output_format = run_easy_test("test23.ref", built_in_parser)

    assert output_format[0] == "R05-TextFromTree e = e"
    assert output_format[1] == "Extern e = '$EXTERN ' e ';\\n'"
    assert output_format[2] == "Function s (e) t e = e s '\\n'"
    assert output_format[3] == "Entry  = '$ENTRY '"
    assert output_format[4] == "Local  = "
    assert output_format[5] == "Sentences e = e"
    assert output_format[6] == "*TextFromSentence ((e) (e)) = '  ' e ';\\n'"
    assert output_format[7] == "Native (e s) e = '* file: \"' e '%%\\n'"
    assert output_format[8] == "*FlatLines e = e"
    assert output_format[9] == "Symbol s e = e"
    assert output_format[10] == "Char s = '\\' s e '\\'"
    assert output_format[11] == "Number s = e"
    assert output_format[12] == "Name t e = e"
    assert output_format[13] == "Variable s e = s '.' e"
    assert output_format[14] == "Brackets e = '(' e ')'"
    assert output_format[15] == "CallBrackets e = '<' e '>'"
    assert output_format[16] == "TextFromExpr e = e"
    assert output_format[17] == "*TextFromExpr-Char e = s e"
    assert output_format[18] == "*TextFromTerm (s e) = e"
    assert output_format[19] == "EscapeChar s = s e"
    assert output_format[20] == "*EscapeChar-Aux s s = s e"
    assert output_format[21] == "*EscapeChar-SwCompare s s s s = s e"
    assert output_format[22] == "*CharFromHex s = s"


@pytest.mark.timeout(1)
def test_24(built_in_parser):
    output_format = run_easy_test("test24.ref", built_in_parser)

    assert output_format[0] == "*F s s s s = s"
    assert output_format[1] == "*G s s s s = s"
    assert output_format[2] == "*H s s e = s"


@pytest.mark.timeout(1)
def test_25(built_in_parser, capsys):
    _ = run_easy_test("test25.ref", built_in_parser)

    captured = capsys.readouterr()
    output = re.sub(r'\.[\d]+', '', captured.err)
    assert output == "Function F, sentence 0, there isn't solution for equation: 'a' () 'z' 'z' 'z' 'z' : in[F] => s s () e\n"


@pytest.mark.timeout(1)
def test_26(built_in_parser):
    output_format = run_easy_test("test26.ref", built_in_parser)

    assert output_format[0] == "*EL-Create  = (ErrorList)"
    assert output_format[1] == "*EL-AddErrorAt (ErrorList e) t e = (ErrorList e (t e))"
    assert output_format[2] == "*EL-AddUnexpected (ErrorList e) (s t e) e = (ErrorList e (t e))"
    assert output_format[3] == "*EL-Destroy (ErrorList e) = e"
    assert output_format[4] == "StrFromToken s e = s e s"


@pytest.mark.timeout(1)
def test_27(built_in_parser):
    output_format = run_easy_test("test27.ref", built_in_parser)

    assert output_format[0] == "*F  = 1 2 3"
    assert output_format[1] == "*G 1 2 3 4 5 = "
    assert output_format[2] == "H 4 5 = "


@pytest.mark.timeout(1)
def test_28(built_in_parser):
    output_format = run_easy_test("test28.ref", built_in_parser)

    assert output_format[0] == "*F e s = "
    assert output_format[1] == "*G (e) e = "
    assert output_format[2] == "*H (e) e s = "


@pytest.mark.timeout(1)
def test_29(built_in_parser):
    output_format = run_easy_test("test29.ref", built_in_parser)

    assert output_format[0] == "*F t = "
    assert output_format[1] == "*F2 t = "
    assert output_format[2] == "*F3 t = "


@pytest.mark.timeout(1)
def test_30(built_in_parser):
    output_format = run_easy_test("test30.ref", built_in_parser)

    assert output_format[0] == "*G (e) e = e"
    assert output_format[1] == "*F s e = s"


@pytest.mark.timeout(1)
def test_31(built_in_parser):
    output_format = run_easy_test("test31.ref", built_in_parser)

    assert output_format[0] == "*G (e) e = e"
    assert output_format[1] == "*F s e = s"


@pytest.mark.timeout(1)
def test_32(built_in_parser):
    output_format = run_easy_test("test32.ref", built_in_parser)

    assert output_format[0] == "*F t e = t"
    assert output_format[1] == "*G e t = t"
    assert output_format[2] == "*H e t = e"


@pytest.mark.timeout(1)
def test_33(built_in_parser):
    output_format = run_easy_test("test33.ref", built_in_parser)

    assert output_format[0] == "*F (((t))) = "
    assert output_format[1] == "*F2 ((t)) = "
    assert output_format[2] == "*F3 (((t))) = "


@pytest.mark.timeout(1)
def test_34(built_in_parser):
    output_format = run_easy_test("test34.ref", built_in_parser)

    assert output_format[0] == "*F I I I e = "
    assert output_format[1] == "*F2 I I e = "
    assert output_format[2] == "*F3 I I I e = "


@pytest.mark.timeout(1)
def test_35(built_in_parser):
    output_format = run_easy_test("test35.ref", built_in_parser)

    assert output_format[0] == "*Derivative t = t"
    assert output_format[1] == "*Opt t = t"
    assert output_format[2] == "*Opt-Rules t s t = t"
    assert output_format[3] == "DerivOpt t = t"


