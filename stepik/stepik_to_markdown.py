import sys
from html.parser import HTMLParser

def stepik_to_markdown(s):

    predata = ['---', '\n', 'pagetitle: Stepik', '\n', '---', '\n']

    class Marker:
        pass

    NumberedList = Marker()
    UnnumberedList = Marker()

    tags  = {}

    stack = []
    link  = []
    do_not_escape = []
    in_pre = []

    def prepare_data(data):
        def escape(data):
            if not data or len(do_not_escape):
                return data
            escapeable = [ '\\', '`', '*', '{', '}', '[', ']', '(',
                           ')',  '#', '+', '-', '.', '!', '_', '>' ]
            for e in escapeable:
                data = data.replace(e, '\\' + e)
            return data

        if data[0:2] == "$$":
            return data

        fms = data.split("$")
        sb = ""
        se = "" if len(fms) % 2 else "\\$" + fms.pop()
        fm = False
        for i in range(0, len(fms)):
            if fm:
                sb += "$" + fms[i].strip() + "$"
            else:
                sb += escape(fms[i])
            fm = not fm
        return sb + se

    class StepikHTMLParser(HTMLParser):

        def handle_starttag(self, tag, attrs):
            if tag == 'br':
                predata.append("\\")
                predata.append("\n")
            elif tag == 'b':
                predata.append("**")
            elif tag == 'i':
                predata.append("*")
            elif tag == 'h1':
                predata.append("\n# ")
            elif tag == 'h2':
                predata.append("\n## ")
            elif tag == 'ul':
                predata.append("\n")
                stack.append(UnnumberedList)
            elif tag == 'ol':
                predata.append("\n")
                stack.append(NumberedList)
            elif tag == 'li':
                pr = ("  " * len(stack))
                pr += "- " if stack[-1] == UnnumberedList else "1. "
                predata.append(pr)
            elif tag == 'p':
                predata.append("\n")
            elif tag == 'a':
                for (k, v) in attrs:
                    if k == 'href':
                        link.append(v)
                        break
                predata.append('[')
            elif tag == 'span':
                pass
            elif tag == 'img':
                alt = ""
                for k, v in attrs:
                    if k == 'alt':
                        alt = v
                    elif k == 'src':
                        src = v
                predata.append("![%s](%s)" % (alt, src))
            elif tag == 'code':
                if in_pre:
                    predata.append("```" + (attrs[0][1] if len(attrs) else ''))
                    predata.append("\n")
                else:
                    predata.append(' `')
                do_not_escape.append(())
            elif tag == 'pre':
                in_pre.append(True)
                predata.append("\n")
            else:
                raise ValueError(tag)

        def handle_endtag(self, tag):
            if tag == 'pre':
                in_pre.pop()
                predata.append("\n")
            elif tag == 'span':
                pass
            elif tag == 'code':
                if in_pre:
                    predata.append("\n")
                    predata.append("```")
                else:
                    predata.append('` ')
                do_not_escape.pop()
            elif tag in {'h1', 'h2'}:
                predata.append("\n")
            elif tag == 'b':
                predata.append("**")
            elif tag == 'i':
                predata.append("*")
            elif tag == 'a':
                predata.append('](' + link[-1] + ')')
                link.pop()
            elif tag == 'p':
                predata.append("\n")
            elif tag in {'ol', 'ul'}:
                stack.pop()
            elif tag in {'li'}:
                if predata[-1] != "\n":
                    predata.append("\n")
            else:
                raise ValueError(tag)

        def handle_data(self, data):
            predata.append(prepare_data(data.strip()))

    parser = StepikHTMLParser()
    parser.feed(s)
    return "".join(predata)

# print(stepik_to_markdown(sys.stdin.read()))
