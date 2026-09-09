import re
import numpy as np

from .opFormat import FUNC_FORMAT

class opParse:
    def __init__(self, pnames=None, videArgSymb=["_", "\\", "#"]):
        self.funcDict = FUNC_FORMAT
        self.videArgSymb = videArgSymb
        self.pnames = pnames

    def convert(self, opExpress):
        self.raw_opExpress = opExpress # Class to be a class
        self.relatPara = []
        self.log = []
        self.warning = 0
        self.error = 0
        
        opExpress = opExpress.replace("\'","\"").replace("\\\"","\'")
        opExpress_useful = "".join(opExpress.replace("!=","").split("\"")[::2])
        if "&&" in opExpress_useful or "||" in opExpress_useful or "!" in opExpress_useful:
            opExpress = opExpress.replace("&&", " and ").replace("||", " or ").replace("!=", "~=").replace("!", " not ").replace("~=", "!=")
        result, typ = self._func_convert(opExpress)
        if typ not in ["Unknown", "num"]:
            self.log.append(f"|[Error]| [{opExpress}]必须为数值")
            self.error += 1
        self.opExpress = result # Class to be a class
        return result

    def _func_convert(self, opExpress, seqs_=[]):
        seqs = seqs_.copy()
        opExpress_ = opExpress = re.sub(r" +", " ", opExpress)
        opExpress_split = list(re.finditer(r"[a-zA-Z\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*\(", opExpress))
        for r_split in reversed(opExpress_split):
            a, b = r_split.span()
            if opExpress[a:b-1] not in ["and", "or", "xor", "not"]: # Special Functions "funcName("
                ## Focus on Function Name
                func_name = opExpress[a:b-1]
                
                ### Focus on Expression (In this case, expression must be packed by "()")
                left = 1
                for i in range(b, len(opExpress)):
                    if left == 0:
                        break
                    if opExpress[i] == "(":
                        left += 1
                    elif opExpress[i] == ")":
                        left -= 1
                        if left == 0 and i == len(opExpress) - 1:
                            i += 1
                            break
                if left > 0:
                    i = len(opExpress) + 1
                opExpress_origin = self._backlog(opExpress[a:i], seqs)
                
                if left > 0:
                    self.log.append(f"|[Warning]| [{opExpress_origin}]缺少{left-1}个\")\"")
                    self.warning += 1
                    args = (opExpress[b:]+")"*(left-1)).split(",")
                else:
                    args = opExpress[b:i-1].split(",")
                    
                ## Translate Expression
                if func_name in self.funcDict.keys():
                    args_need, func_out, multinput = self.funcDict[func_name]
                    result, seqs = self._convert_args(args, args_need, multinput, opExpress_origin, seqs, func_name)
                    if result is None:
                        seqs.append(([func_name, None], "Unknown", opExpress_origin))
                    else:
                        seqs.append(([func_name]+result, func_out, opExpress_origin))
                elif func_name in self.relatPara:
                    pn = f"P{self.relatPara.index(func_name)}"
                    self.relatPara.append(func_name)
                    seqs.append(([pn]+[self._stringconvert(arg, seqs)[0] for arg in args], "Unknown", opExpress_origin))
                elif self.pnames is None or func_name not in self.pnames and (func_name not in dir(np), func_name not in dir(np.linalg)):
                    pn = f"P{len(self.relatPara)}"
                    self.relatPara.append(func_name)
                    seqs.append(([pn]+[self._stringconvert(arg, seqs)[0] for arg in args], "Unknown", opExpress_origin))
                else:
                    self.log.append(f"|[Error]| {opExpress_origin}函词{func_name}未定义")
                    self.error += 1
                    if args[0].replace(" ",""):
                        seqs.append(([func_name]+[self._stringconvert(arg, seqs)[0] for arg in args], "Unknown", opExpress_origin))
                    else:
                        seqs.append(([func_name], "Unknown", opExpress_origin))
                opExpress = f"{opExpress[:a]} 00seqs_{len(seqs)-1}_ {opExpress[i:]}"

        if not opExpress.replace(" ",""):
            return None, "Unknown"
        if "[" in opExpress or "{" in opExpress or "]" in opExpress or "}" in opExpress:
            self.log.append(f"|[Warning]| {opExpress_} 中存在非函词的特殊括号")
            self.warning += 1
        opExpress = self._complete(opExpress.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")"), seqs)
        result, typ = self._stringconvert(opExpress, seqs)
        return result, typ
    
    def _convert_args(self, args, args_need, multinput, opExpress_origin, seqs_, func_name):
        seqs = seqs_.copy()
        if len(args) > len(args_need):
            if not multinput:
                self.log.append(f"|[Warning]| [{opExpress_origin}]输入过多")
                self.warning += 1
            else:
                args_need.extend([args_need[-1]]*(len(args) - len(args_need))) 
        args_ = [None]*len(args_need)
        for func_pos, typin, typwant, arg_default in args_need:
            if func_pos >= len(args):
                if arg_default is None:
                    self.log.append(f"|[Error]| [{opExpress_origin}]缺少输入{func_pos}")
                    self.error += 1
                elif arg_default != "NoneType":
                    args_[func_pos] = arg_default
            elif typin == "rule": ## rule[xxx]
                args[func_pos] = re.sub(r" +", " ", args[func_pos])
                if args[func_pos][:1] == " ":
                    args[func_pos] = args[func_pos][1:]
                if args[func_pos][-1:] == " ":
                    args[func_pos] = args[func_pos][:-1]
                if args[func_pos][:1] == "\"":
                    args[func_pos] = args[func_pos][1:]
                if args[func_pos][-1:] == "\"":
                    args[func_pos] = args[func_pos][:-1]
                if not args[func_pos].replace(" ","") or args[func_pos].replace(" ","") in self.videArgSymb:
                    if arg_default is None:
                        self.log.append(f"|[Error]| [{opExpress_origin}]缺少输入{func_pos}")
                        self.error += 1
                    elif arg_default != "NoneType":
                        args_[func_pos] = arg_default
                else:
                    result, typreal = self._stringconvert(args[func_pos], seqs)
                    arg = self._backlog(args[func_pos], seqs)
                    if typreal not in ["Unknown", typwant]:
                        self.log.append(f"|[Error]| [{opExpress_origin}]输入{func_pos}为{typreal}类型(应为{typwant}类型)")
                        self.error += 1
                    else:
                        args_[func_pos] = result
            else: ## xxx
                if not args[func_pos].replace(" ","")  or args[func_pos].replace(" ","") in self.videArgSymb:
                    if arg_default is None:
                        self.log.append(f"|[Error]| [{opExpress_origin}]缺少输入{func_pos}")
                        self.error += 1
                    elif arg_default != "NoneType":
                        args_[func_pos] = arg_default
                    continue
                if typwant == "num":
                    arg_ = args[func_pos].replace(" ","")
                    if args[func_pos][0] == "0" and len(args[func_pos])>1:
                        if args[func_pos][1] == "x":
                            try:
                                args_[func_pos] = int(args[func_pos],base=16)
                            except Exception as e:
                                self.log.append(f"|[Error]| {args[func_pos]}不可解析")
                                self.error += 1
                            continue
                        elif args[func_pos][1]== "b":
                            try:
                                args_[func_pos] = int(arg_,base=2)
                            except Exception as e:
                                self.log.append(f"|[Error]| {arg_}不可解析")
                                self.error += 1
                            continue
                        elif arg_[1] == "o":
                            try:
                                args_[func_pos] = int(arg_,base=8)
                            except Exception as e:
                                self.log.append(f"|[Error]| {arg_}不可解析")
                                self.error += 1
                            continue
                    try:
                        args_[func_pos] = float(args[func_pos].replace(" ",""))
                    except Exception as e:
                        try:
                            args_[func_pos] = float(eval(args[func_pos]))
                            self.log.append(f"|[Warning]| [{opExpress_origin}]输入{func_pos}不应为表达式")
                            self.warning += 1
                        except Exception as e:
                            if not arg_default is None:
                                args_[func_pos] = arg_default
                                self.log.append(f"|[Warning]| [{opExpress_origin}]输入{func_pos}无法解析")
                                self.warning += 1
                            else:
                                self.log.append(f"|[Error]| [{opExpress_origin}]输入{func_pos}无法解析")
                                self.error += 1
                elif typwant == "bool":
                    if args[func_pos].lower() == "true":
                        args_[func_pos] = True
                    elif args[func_pos].lower() == "false":
                        args_[func_pos] = False
                    elif args[func_pos].lower() not in ["none", "null"]:
                        if not arg_default is None:
                            args_[func_pos] = arg_default
                        if not arg_default is None:
                            args_[func_pos] = arg_default
                            self.log.append(f"|[Warning]| [{opExpress_origin}]输入{func_pos}无法解析")
                            self.warning += 1
                        else:
                            self.log.append(f"|[Error]| [{opExpress_origin}]输入{func_pos}无法解析")
                            self.error += 1
                elif typwant == "pname":
                    arg_ = args[func_pos].replace(" ","").replace("\"","")
                    if not self.pnames is None and arg_ not in self.pnames:
                        if not arg_default is None:
                            args_[func_pos] = arg_default
                            self.relatPara.add(arg_default)
                            self.log.append(f"|[Warning]| [{opExpress_origin}]输入{func_pos}参数名[{arg_}]无法解析")
                            self.warning += 1
                        else:
                            args_[func_pos] = arg_
                            self.log.append(f"|[Error]| [{opExpress_origin}]输入{func_pos}参数名[{arg_}]无法解析")
                            self.error += 1
                    else:
                        if arg_ not in self.relatPara:
                            args_[func_pos] = f"P{len(self.relatPara)}"
                            self.relatPara.append(arg_)
                        else:
                            args_[func_pos] = f"P{self.relatPara.index(arg_)}"
                else:
                    args_[func_pos] = arg_default
            
        return args_, seqs

    ## 补全括号
    def _complete(self, opExpress, seqs_):
        seqs = seqs_.copy()
        left = 0; l = 0; cons = True
        if "(" in opExpress or ")" in opExpress:
            for i in range(len(opExpress)):
                if opExpress[i + l] == "\"":
                    cons = not cons
                if not cons:
                    continue
                if opExpress[i + l] == "(":
                    left += 1
                elif opExpress[i + l] == ")":
                    left -= 1
            if not cons:
                self.log.append(f"|[Error]| [{self._backlog(opExpress,seqs)}] 引号不匹配")
                self.error += 1
                opExpress += "\""
            if left < 0:
                self.log.append(f"|[Error]| [{self._backlog(opExpress,seqs)}] 缺少{-left}个\"\(\"")
                self.error += 1
                opExpress = "("*(-left) + opExpress
            elif left > 0:
                self.log.append(f"|[Error]| [{self._backlog(opExpress,seqs)}] 缺少{left}个\"\)\"")
                self.error += 1
                opExpress += ")"*left
        return opExpress

    ## Treat "\""
    def _stringconvert(self,opExpress,seqs_):
        seqs = seqs_.copy()
        opExpress_ = opExpress
        opExpress = opExpress_.replace("=","==").replace("====","==").replace("!==","!=").replace("<==","<=")\
               .replace(">==",">=").replace("（","(").replace("）",")").replace("，",",")\
               .replace("！","!")
        if opExpress != opExpress_:
            self.log.append(f"|[Warning]| [{self._backlog(opExpress_, seqs)}]存在非法字符")
            self.warning += 1
        if "," in opExpress:
            opExpress, opExpress_ = opExpress.split(",",1)
            self.log.append(f"|[Error]| [{self._backlog(opExpress_, seqs)}]为多余部分")
            self.error += 1
        return self._parentheseconvert(self._complete(opExpress,seqs),seqs)

    ## Treat "()"
    def _parentheseconvert(self,opExpress,seqs_):
        seqs = seqs_.copy()
        opExpress_ = opExpress = re.sub(r" +"," ",opExpress)
        opExpress = re.sub(r"\( *\)","",opExpress)
        if not opExpress.replace(" ",""):
            return None, "Unknown"
        if opExpress[:1] == " ":
            opExpress = opExpress[1:]
        if opExpress[-1:] == " ":
            opExpress = opExpress[:-1]
        opExpress_origin = self._backlog(opExpress_, seqs)
        warnComplet = False
        while "(" in opExpress or ")" in opExpress:
            if "(" in opExpress and not ")" in opExpress:
                opExpress += ")"
                if not warnComplet:
                    self.log.append(f"|[Error]| [{opExpress_origin}]缺少\"(\"")
                    self.error += 1; warnComplet = True
            elif ")" in opExpress and not "(" in opExpress:
                opExpress = "(" + opExpress
                if not warnComplet:
                    self.log.append(f"|[Error]| [{opExpress_origin}]缺少\")\"")
                    self.error += 1; warnComplet = True
            if opExpress[0] == "(" and opExpress[-1] == ")" and "(" not in opExpress[1:-1]:
                result, typ = self._plusminusconvert(opExpress[1:-1], seqs)
                return result, typ
            l = 0
            for subopExpress in re.finditer(r"\([^\(\)]+\)",opExpress):
                a,b = subopExpress.span()
                result, typ = self._plusminusconvert(opExpress[a-l+1:b-l-1], seqs)
                seqs.append((result, typ,self._backlog(opExpress[a-l+1:b-l-1],seqs)))
                opExpress = "%s 00seqs_%d_ %s"%(opExpress[:a], len(seqs)-1 ,opExpress[b:])
                l += (b-a) - (9 + len(str(len(seqs)-1)))
        result, typ = self._plusminusconvert(opExpress,seqs)
        return result, typ

    ## Treat +/-(Ignore negative sign)
    def _plusminusconvert(self,opExpress,seqs_):
        seqs = seqs_.copy()
        opExpress = opExpress.replace(" ","")
        opExpress_origin = self._backlog(opExpress,seqs)
        if "+-" in opExpress or "-+" in opExpress or "++" in opExpress:
            self.log.append(f"|[Warning]| [{opExpress_origin}] 存在冗余正号")
            self.warning += 1
        if "--" in opExpress:
            self.log.append(f"|[Warning]| [{opExpress_origin}] 存在负号与减号的叠加")
            self.warning += 1
        while "--" in opExpress or "+-" in opExpress or "-+" in opExpress:
            opExpress = opExpress.replace("--", "+").replace("-+", "-").replace("+-", "-").replace("++", "+")
        result = []
        opExpress_split = list(re.finditer(r"\+|-",opExpress))
        a_ = 0
        if not opExpress_split:
            result, typ = self._proddivconvert(opExpress,seqs)
            return result, typ
        else:
            len_split = len(opExpress_split)
            for i in range(len_split):
                a,b = opExpress_split[i].span()
                opExpress1 = opExpress[a_:a]
                if not opExpress1 or opExpress[a-1] in ["*","/","^","|","&","%","~"] or \
                   (opExpress[a-1].lower() == "e" and (a==1 or opExpress[a-2] in [' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])):
                    continue
                opExpress_a, typ = self._proddivconvert(opExpress1,seqs)
                if typ not in ["num","Unknown"]:
                    self.log.append(f"|[Error]| [{self._backlog(opExpress1,seqs)}] {opExpress[a:b]}前非数值类型")
                    self.error += 1
                if result:
                    if former == "+":
                        result[1].append(opExpress_a)
                    else:
                        result.append(opExpress_a)
                    former = opExpress[a:b]
                else:
                    result = ["-",["+",opExpress_a]]
                    former = opExpress[a:b]
                a_ = b
            opExpress1 = opExpress[a_:]
            if not opExpress1:
                self.log.append("|[Error]| 句末多余加减号")
                self.error += 1
            else:
                opExpress_a, typ = self._proddivconvert(opExpress1,seqs)
                if typ not in ["num","Unknown"]:
                    self.log.append(f"|[Error]| [{self._backlog(opExpress1,seqs)}]{opExpress[a:b]}前非数值类型")
                    self.error += 1
                if result:
                    if former == "+":
                        result[1].append(opExpress_a)
                    else:
                        result.append(opExpress_a)
                else:
                    result = ["-",["+",opExpress_a]]
            if len(result) == 2:
                result =result[1]   # multi-plus
                if len(result) == 2:
                    result = result[1]
            elif len(result[1]) == 2:
                result = ["-", result[1][1]] + result[2:] # multi-minus
        return result, "num"

    ## Treat *|/|//|%
    def _proddivconvert(self,opExpress,seqs_):
        seqs = seqs_.copy()
        opExpress = opExpress.replace(" ","").replace("**","=") ## Replace "**" with "=" which exists no more
        result = []
        opExpress_split = list(re.finditer(r"\*|//?|%",opExpress))
        if not opExpress_split:
            result, typ = self._powerconvert(opExpress.replace("=","**"),seqs)
            return result, typ
        else:
            len_split = len(opExpress_split)
            for i in range(len_split):
                a,b = opExpress_split[i].span()
                if i == len_split-1:
                    fin = len(opExpress)
                else:
                    fin = opExpress_split[i+1].span()[0]
                opExpress_ = opExpress[b:fin]
                if not opExpress_:
                    opExpress_ = None
                    self.log.append(f"|[Error]| [{self._backlog(opExpress.replace('=','**'),seqs)}]中两乘除号间缺少成分")
                    self.error += 1
                else:
                    opExpress_a, typ = self._powerconvert(opExpress_.replace("=","**"),seqs)
                    if typ not in ["num","Unknown"]:
                        self.log.append(f"|[Error]| [{self._backlog(opExpress_.replace('=','**'),seqs)}] {opExpress[a:b]}后非数值类型")
                        self.error += 1
                    opExpress_ = opExpress_a
                func_name = opExpress[a:b].replace(" ","")
                if result:
                    if func_name == "*":
                        result[1].append(opExpress_)
                    elif func_name == "/":
                        result.append(opExpress_)
                    else:
                        if len(result) == 2:
                            result =result[1]
                            if len(result) == 2:
                                result = result[1]
                        elif len(result[1]) == 2:
                            result = ["/", result[1][1]]+result[2:]
                        result = ["/",["*",result]]
                else:
                    opExpress1 = opExpress[:a]
                    if not opExpress1.replace(" ",""):
                        opExpress1 = None
                        self.log.append(f"|[Error]| [{self._backlog(opExpress.replace('=','**'),seqs)}]中两乘除关联词间缺少成分")
                        self.error += 1
                    else:
                        opExpress_a, typ = self._powerconvert(opExpress1.replace("=","**"),seqs)
                        if typ not in ["num","Unknown"]:
                            self.log.append(f"|[Error]| [{self._backlog(opExpress1.replace('=','**'),seqs)}]{opExpress[a:b]}前非数值类型")
                            self.error += 1
                        opExpress1 = opExpress_a
                    if func_name == "*":
                        result = ["/",["*",opExpress1,opExpress_]]
                    elif func_name == "/":
                        result = ["/",["*",opExpress1],opExpress_]
                    else:
                        result = ["/",["*",[func_name,opExpress1,opExpress_]]]
            if len(result) == 2:
                result =result[1]
                if len(result) == 2:
                    result = result[1]
            elif len(result[1]) == 2:
                result = ["/", result[1][1]]+result[2:]
        return result, "num"

    ## Treate(**)
    def _powerconvert(self,opExpress,seqs_):
        seqs = seqs_.copy()
        opExpress = opExpress.replace(" ","")
        result = []
        if "***" in opExpress:
            self.log.append(f"|[Error]| [{self._backlog(opExpress[b:fin],seqs)}]中两(阶)乘号\"***\"间缺少成分")
            self.error += 1
            opExpress = re.sub(r"\*\*\**", "**", opExpress)
        opExpress_split = list(re.finditer(r"\*\*", opExpress))
        if not opExpress_split:
            result, typ = self._bitoperatorconvert(opExpress,seqs)
            return result, typ
        else:
            len_split = len(opExpress_split)
            for i in range(len_split):
                a,b = opExpress_split[i].span()
                if i == len_split-1:
                    fin = len(opExpress)
                else:
                    fin = opExpress_split[i+1].span()[0]
                opExpress_ = opExpress[b:fin]
                if not opExpress_:
                    opExpress_ = None
                    self.log.append(f"|[Error]| [{self._backlog(opExpress[b:fin],seqs)}]中两阶乘号\"**\"间缺少成分")
                    self.error += 1
                else:
                    opExpress_a, typ = self._bitoperatorconvert(opExpress_,seqs)
                    if typ not in ["num","Unknown"]:
                        self.log.append(f"|[Error]| [{self._backlog(opExpress_,seqs)}]  **后为非数值类型")
                        self.error += 1
                    opExpress_ = opExpress_a
                if result:
                    result = ["**",result,opExpress_]
                else:
                    opExpress1 = opExpress[:a]
                    if not opExpress1.replace(" ",""):
                        opExpress1 = None
                        self.log.append(f"|[Error]| [{self._backlog(opExpress[:a],seqs)}]中两阶乘号\"**\"间缺少成分")
                        self.error += 1
                    else:
                        opExpress_a, typ = self._bitoperatorconvert(opExpress1,seqs)
                        if typ not in ["num","Unknown"]:
                            self.log.append(f"|[Error]| [{self._backlog(opExpress1,seqs)}]**前非数值类型")
                            self.error += 1
                        opExpress1 = opExpress_a
                    result = ["**",opExpress1,opExpress_]
        return result, "num"

    ## Treat &| | |^|~ -> Translate value|bool|panme
    def _bitoperatorconvert(self,opExpress,seqs_):
        seqs = seqs_.copy()
        opExpress = opExpress.replace(" ","")
        if not opExpress:
            return None, "Unknown"
        if "~~" in opExpress:
            self.log.append(f"|[Warning]| [{self._backlog(opExpress_,seqs)}]存在冗余~")
            self.warning += 1
            while "~~" in opExpress:
                opExpress = opExpress.replace("~~", "")
        result = []
        opExpress_split = list(re.finditer(r"\^|\||\&",opExpress))
        if not opExpress_split:
            if opExpress[:1] == "~":
                opExpress_ = opExpress[1:]
                opExpress_a, typ = self._bitoperatorconvert(opExpress_,seqs)
                if typ not in ["num","Unknown"]:
                    self.log.append(f"|[Error]| [{self._backlog(opExpress_,seqs)}] {opExpress[a:b]}后非数值类型")
                    self.error += 1
                return ["~", opExpress_a], "num"
            if opExpress[0] == "+":
                opExpress_ = opExpress[1:]
                opExpress_a, typ = self._bitoperatorconvert(opExpress_,seqs)
                if typ not in ["num","Unknown"]:
                    self.log.append(f"|[Error]| [{self._backlog(opExpress_,seqs)}] {opExpress[a:b]}后非数值类型")
                    self.error += 1
                return opExpress_a, "num"
            if opExpress[0] == "-":
                opExpress_ = opExpress[1:]
                opExpress_a, typ = self._bitoperatorconvert(opExpress_,seqs)
                if typ not in ["num","Unknown"]:
                    self.log.append(f"|[Error]| [{self._backlog(opExpress_,seqs)}] {opExpress[a:b]}后非数值类型")
                    self.warning += 1
                    return None, "Unknown"
                if isinstance(opExpress_a, int) or isinstance(opExpress_a, float):
                    return opExpress_a*-1, "num"
                else:
                    return ["*", opExpress_a, -1], "num"
            if opExpress.replace(" ","").lower() in ["inf","np.inf","numpy.inf","math.inf"]:
                return float("inf"), "num"
            elif opExpress.replace(" ","").lower() in ["nan","math.nan","np.nan","numpy.nan"]:
                return float("nan"), "num"
            nums = opExpress.split("00seqs_")
            if len(nums) > 2:
                self.log.append("|[Error]| 存在若干括号附近缺少运算符")
                self.error += 1
                try:
                    result, typ, _ = seqs[int(nums[1][:-1])]
                    return result, typ
                except Exception as e:
                    return None, "Unknown"
            elif len(nums) == 2:
                if nums[0]:
                    self.log.append("|[Error]| 存在若干括号附近缺少运算符")
                    self.error += 1
                try:
                    result, typ, _ = seqs[int(nums[1][:-1])]
                    return result, typ
                except Exception as e:
                    self.log.append("|[Error]| 存在若干括号附近缺少运算符")
                    self.error += 1
                    return None, "Unknown"
            elif "." in opExpress or "e" in opExpress.lower():
                try:
                    return float(opExpress), "num"
                except Exception as e:
                    self.log.append(f"|[Error]| {opExpress}不可解析")
                    self.error += 1
                    return None, "Unknown"
            elif opExpress[0] == "0" and len(opExpress)>1:
                if opExpress[1] == "x":
                    try:
                        return int(opExpress,base=16), "num"
                    except Exception as e:
                        self.log.append(f"|[Error]| {opExpress}不可解析")
                        self.error += 1
                        return None, "Unknown"
                elif opExpress[1]== "b":
                    try:
                        return int(opExpress,base=2), "num"
                    except Exception as e:
                        self.log.append(f"|[Error]| {opExpress}不可解析")
                        self.error += 1
                        return None, "Unknown"
                elif opExpress[1] == "o":
                    try:
                        return int(opExpress,base=8), "num"
                    except Exception as e:
                        self.log.append(f"|[Error]| {opExpress}不可解析")
                        self.error += 1
                        return opExpress, "Unknown"
            else:
                try:
                    return int(opExpress), "num"
                except Exception as e:
                    if self.pnames is None or opExpress in self.pnames:
                        if opExpress not in self.relatPara:
                            self.relatPara.append(opExpress)
                        return f"P{self.relatPara.index(opExpress)}", "num"
                    else:
                        self.log.append(f"|[Error]| {opExpress}不可解析")
                        self.error += 1
                        return opExpress, "Unknown"
        else:
            len_split = len(opExpress_split)
            for i in range(len_split):
                a,b = opExpress_split[i].span()
                if i == len_split-1:
                    fin = len(opExpress)
                else:
                    fin = opExpress_split[i+1].span()[0]
                opExpress_ = opExpress[b:fin]
                if not opExpress_:
                    opExpress_ = None
                    self.log.append(f"|[Error]| [{self._backlog(opExpress[b:fin],seqs)}]中两位操作间缺少成分")
                    self.error += 1
                else:
                    opExpress_a, typ = self._bitoperatorconvert(opExpress_,seqs)
                    if typ not in ["num","Unknown"]:
                        self.log.append(f"|[Error]| [{self._backlog(opExpress[a:b],seqs)}] {opExpress[a:b]}后为非数值类型")
                        self.error += 1
                    opExpress_ = opExpress_a
                func_name = opExpress[a:b]
                if result:
                    result = [func_name,result,opExpress_]
                else:
                    opExpress1 = opExpress[:a]
                    if not opExpress1:
                        opExpress1 = None
                        self.log.append(f"|[Error]| [{self._backlog(opExpress[:a+10],seqs)}]中两位操作间缺少成分")
                        self.error += 1
                    else:
                        opExpress_a, typ = self._bitoperatorconvert(opExpress1,seqs)
                        if typ not in ["num","Unknown"]:
                            self.log.append(f"|[Error]| [{self._backlog(opExpress1,seqs)}] {opExpress[a:b]}后非数值类型")
                            self.error += 1
                        opExpress1 = opExpress_a
                    result = [func_name, opExpress1, opExpress_]
        return result, "num"

    def _backlog(self, opExpress, seqs_):
        if opExpress is None:
            return ""
        if seqs_:
            seqs = seqs_.copy()
            while True:
                nums = re.findall(r"00seqs_([0-9]+)_", f" {opExpress} ")
                if not nums:
                    break
                for num in nums:
                    opExpress = opExpress.replace(f"00seqs_{num}_", f" {seqs[int(num)][2]} ").replace("  ", " ").replace(" ", "  ")
        opExpress = re.sub(r" +"," ", opExpress); opExpress = re.sub(r" *\) *",")", opExpress); opExpress = re.sub(r" *\( *","(", opExpress)
        if opExpress[:1] == " ":
            opExpress = opExpress[1:]
        if opExpress[-1:] == " ":
            opExpress = opExpress[:-1]
        return opExpress

if __name__ == "__main__":
    from pprint import pprint
    op = "10/tan(αa)/(Vxm**2+Vym**2+Vzm**2)"
    prep = opParse()#pnames=["αa", "Vxm", "Vym", "Vzm"])
    print(f">> opExpress String:   {op}\n\n>> Translated opExpress:")
    pprint(prep.convert(op))
    print(f"* Para : \n   ** {list(prep.relatPara)}")
    print(f"\n======== {prep.error} Errors & {prep.warning} Warnings ========")
    print("  * "+"\n  * ".join(prep.log))
