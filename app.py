import streamlit as st
from io import StringIO
import re
import datetime
from code_editor import code_editor


st.title("Fluentd Configuration Generator")
st.markdown(f"Generate Known configuration generator for fluentd Agents")

class Parser():
    def __init__(self,name):
        self.ParserName = name
 
class SourceTail():    
    def __init__(self, path, pos_path=""):
        self.Path  = path
        self.PosPath = pos_path
     
class Source:
    def __init__(self, rule_name,  source_type,  tag, have_parser=False, parser_name="", emit_unmatched_lines=False, path_key="", file_path="", pos_file_path=""):
        self.RuleName = rule_name
        self.Tag = tag
        self.EmitUnmatchedLines = emit_unmatched_lines
        self.PathKey = path_key
        
        if source_type == "tail":
            self.SourceType = source_type
            self.SourceObjectType = SourceTail( file_path, pos_file_path)
        
        self.HaveParser = have_parser
        if self.HaveParser:
            self.Parser = Parser(parser_name)
            
    def __str__(self):
        
        s_ = f"#### RuleName: {self.RuleName}\n"
        s_ += f"##### Author: \'System\'\n"
        s_ += f"##### LastModified: {datetime.datetime.now().isoformat()}\n"
        s_ += "<source>\n"
        if self.SourceType == "tail":
            s_ += f"\t@type {self.SourceType}\n"
            s_ += f"\tpath {self.SourceObjectType.Path}\n"
            s_ += f"\tpos_file {self.SourceObjectType.PosPath}\n"
        
        if self.HaveParser:
            s_ += "\t<parser>\n"
            s_ += f"\t\t@type {self.Parser.ParserName}\n"
            s_ += "\t</parser>\n"
            
        s_ += f"\tpath_key {self.PathKey}\n"
        s_ += f"\temit_unmatched_lines {self.EmitUnmatchedLines}\n"
        s_ += f"\ttag {self.Tag}\n"
        s_ += "</source>\n\n"
        
        return s_

def get_sources(str_file):
    source_pattern = r"\#\s*(?P<rule_name>\s*[\w\s\(\)]+)\r\n(?P<rule_definition>\<source\>[\s\S]+?\<\/source\>)\r\n+" 
    return re.finditer(source_pattern, str_file)


def extract_value(pattern, input_str,  group_name, flag = None):
    if flag:
        res_ = re.search(pattern, input_str, flag)
    else:
        res_ = re.search(pattern, input_str)
        
    if len(res_.groups()) == 0:
        print(f"Not able to extract the {group_name}")
        return None
    else:
        if group_name in res_.groupdict().keys():
            # print(res_.group(group_name))
            return res_.group(group_name)
        else:
            print(f"Not able to extract the {group_name}, available results {res_.groupdict()}")

def parse_source_config(source_, rule_name):
    # Try to extract the below for each of the source_
    extracted_tag = extract_value(r"^\s+tag\s(?P<tag>[\w\.]+)", source_,  "tag", re.RegexFlag.MULTILINE)
    extracted_source_type = extract_value(r"^\s+@type\s(?P<type>\w+)", source_,  "type", re.RegexFlag.MULTILINE)
    extracted_emit_unmatched_lines = extract_value(r"^\s+emit_unmatched_lines (?P<emit_unmatched_lines>\w+)", source_,  "emit_unmatched_lines", re.RegexFlag.MULTILINE)
    extracted_path_key = extract_value(r"^\s+path_key\s+(?P<path_key>\w+)", source_,  "path_key", re.RegexFlag.MULTILINE)


    extracted_parser = extract_value( r"^\s+<parse>\s*@type (?P<parse_type>\w+)\s+<\/parse>", source_,  "parse_type", re.RegexFlag.MULTILINE)
    if extracted_parser == None:
        extracted_have_parser = False
    else:
        extracted_have_parser = True
    extracted_parser_name = extracted_parser


    extracted_source_type = extract_value( r"^\s+@type\s(?P<type>\w+)", source_,  "type", re.RegexFlag.MULTILINE)

    if extracted_source_type =="tail":
        extracted_source_path = extract_value( r"^\s+path\s+(?P<tail_path>[\w\/\-\.]+)", source_,  "tail_path", re.RegexFlag.MULTILINE)
        extracted_source_pos_path = extract_value( r"^\s+pos_file\s+(?P<tail_pos_file>[\w\/\-\.]+)", source_,  "tail_pos_file", re.RegexFlag.MULTILINE)
        

    #   def __init__(self, rule_name,  source_type,  tag, have_parser=False, parser_name="", emit_unmatched_lines=False, path_key="", file_path="", pos_file_path=""):
    parsed_source = Source(
        rule_name = rule_name,
        source_type = extracted_source_type,
        tag = extracted_tag,
        have_parser = bool(extracted_have_parser),
        parser_name = extracted_parser_name,
        emit_unmatched_lines = bool(extracted_emit_unmatched_lines),
        path_key = extracted_path_key,
        file_path = extracted_source_path,
        pos_file_path = extracted_source_pos_path)
    return parsed_source

all_parsed_source_objects = []

MANDATOR_RULE_FIELDS = ["RuleName","Tag"]

with st.expander("📂 Upload Fluentd Config File"):
    uploaded_file = st.file_uploader("Upload a .conf file", type=["conf"])
    if uploaded_file:
        bytes_data = uploaded_file.getvalue()
        x = bytes_data.decode('utf-8')
        for i in get_sources(x):        
            all_parsed_source_objects.append(parse_source_config(i.group("rule_definition"), i.group("rule_name")))
        custom_btns = [{"name": "Copy", "hasText": True, "alwaysOn": True, "commands": ["copyAll"],
   "style": {"top": "0.46rem", "right": "0.4rem"}}]
        print(f"Parsed Source configurations {len(all_parsed_source_objects)}")
        for  i in all_parsed_source_objects:
            # st.write(str(i))
            with st.expander(i.RuleName):
                with st.form(i.RuleName):
                    header = st.columns([4,5])
                    row1 = st.columns([4,5])
                    new_rule_name  = row1[0].text_input(value=i.RuleName, label="RuleName")
                    new_tag  = row1[1].text_input(value=i.Tag, label="Tag")
                    row2 = st.columns([4,5])
                    is_emmit_onmatched  = row2[0].toggle(value=i.EmitUnmatchedLines, label="EmitUnmatchedLines")
                    new_path_key = row2[1].text_input(value= i.PathKey, label="PathKey")
                    if i.SourceType == "tail":
                        ct1 = st.container(border=True)
                        row3 =  ct1.columns([4,5])
                        row4 =  ct1.columns([4,5])
                        selected = row3[0].selectbox(label="Source Type", options=["tail"], index=0) 
                        new_file_path = row3[1].text_input(value= i.SourceObjectType.Path, label="tail.path")
                        new_pos_path = row4[1].text_input(value= i.SourceObjectType.PosPath, label="tail.pos_path")
                    
                        
                    ct2 = st.container(border=True)
                    row5 = ct2.columns([4,5])
                    new_have_parser  = row5[0].toggle(value=i.HaveParser, label="HaveParser", key="HaveParser"+i.RuleName)
                
                    if i.HaveParser:
                        selected_parser = row5[1].selectbox(label="ParserName", options=[None,"json"], index=0, key="ParserNameSelector"+i.RuleName) 
                    
                    is_clicked =st.form_submit_button('Update data')
                    
                    
                    # on submit button click
                    if is_clicked:
                        st.info("Fields are Updated, Please download the latest file with changes")
                        i.RuleName = new_rule_name
                        i.Tag = new_tag
                        i.EmitUnmatchedLines = is_emmit_onmatched
                        i.PathKey = new_path_key
                        if selected == "tail":
                            i.SourceObjectType.Path = new_file_path 
                            i.SourceObjectType.PosPath = new_pos_path
                        
                        if new_have_parser:
                            i.Parser.ParserName = selected_parser
                            
                with st.expander(label="RawLog"):
                    response_dict = code_editor(str(i), buttons=custom_btns)
                    if response_dict and response_dict['id']:
                        st.write(response_dict)
