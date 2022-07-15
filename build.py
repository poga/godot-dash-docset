import sqlite3, os, re
from urllib.parse import unquote, quote
from bs4 import BeautifulSoup, NavigableString, Tag


con = sqlite3.connect("./Godot.docset/Contents/Resources/docSet.dsidx")
cur = con.cursor()

try: cur.execute('DROP TABLE searchIndex;')
except: pass

cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

docpath = 'Godot.docset/Contents/Resources/Documents'
indexPagePath =os.path.join(docpath, "index.html")
soup = BeautifulSoup(open(indexPagePath).read())

def dashAnchor(entryType, entryName, id):
    if not id:
        id = ""
    tag = BeautifulSoup(f"<a name=\"//apple_ref/cpp/{entryType}/{entryName}\" class=\"dashAnchor\" id=\"{id}\"></a>")
    return tag

def parseClass(relpath):
    filepath = os.path.join(docpath, relpath)
    soup = BeautifulSoup(open(filepath).read())
    print(soup.title)

    # Title
    h1 = soup.select_one('h1')
    if h1:
        h1.insert(0, dashAnchor('Class', h1.text.strip(), False))

    # Constants
    consts = soup.select("section[id=constants] > ul > li > p > strong:first-child")
    for c in consts:
        anchor = f"constants-{c.text}"
        href = relpath + "#" + anchor
        c.insert(0, dashAnchor('Constant', c.text, anchor ))
        print('indexing constant ', c.text, ' ', href)
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (c.text, 'Constant', href))


    # signals
    signals = soup.select("section[id=signals] > ul > li > p > strong")
    for s in signals:
        if s.text != '(' and s.text != ')':
            anchor = f"signals-{s.text}"
            href = relpath + "#" + anchor
            s.insert(0, dashAnchor('Callback', s.text, anchor))
            print('indexing callback ', s.text, ' ', href)
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (s.text, 'Callback', href))

    # enums
    enums = soup.select("section[id=enumerations] > p > strong")
    for e in enums:
        anchor = f"enumerations-{e.text}"
        href = relpath + "#" + anchor
        print('indexing enum ', e.text, ' ', href)
        e.insert(0, dashAnchor('Enum', e.text, anchor))
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (e.text, 'Enum', href))

    #properties
    props = soup.select("section[id=property-descriptions] > ul > li > p > strong")
    for p in props:
        anchor = f"properties-{p.text}"
        href = relpath + "#" + anchor
        print('indexing property ', p.text, ' ', href)
        p.insert(0, dashAnchor('Property', p.text, anchor ))
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (p.text, 'Property', href))
        print(p)

    #methods
    methods = soup.select("section[id=method-descriptions] > ul > li > p > strong")
    for m in methods:
        if m.text != '(' and m.text != ')':
            anchor = f"methods-{m.text}"
            href = relpath + "#" + anchor
            print('indexing method ', m.text, ' ', href)
            m.insert(0, dashAnchor('Method', m.text, anchor))
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (m.text, 'Method', href))

    #remove sidebar
    sidebar = soup.select_one('nav.wy-nav-side')
    if sidebar:
        sidebar.extract()

    with open(filepath, 'w') as out:
        out.write(str(soup))



# Top level
for tag in soup.select("li.toctree-l1 > a"):
    href = tag.attrs['href'].strip()
    name = tag.text
    print('indexing guide ', name)
    cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (name, 'Guide', href))

# second level
any = re.compile(".*")
for tag in soup.select("li.toctree-l2 > a"):
    href = tag.attrs['href'].strip()
    name = tag.text
    if href.startswith('classes/'):
        print('indexing class ', name)
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (name, 'Class', href))
        parseClass(unquote(href))
    else:
        print('indexing guide ', name)
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (name, 'Guide', href))




con.commit()
con.close()

