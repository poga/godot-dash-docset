import sqlite3, os, re
from urllib.parse import unquote
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

def dashAnchor(soup, entryType, entryName):
    tag = soup.new_tag('a', {"name":f"//apple_ref/godot/{entryType}/{entryName}", "class":"dashAnchor"})
    return tag

def parseClass(relpath):
    filepath = os.path.join(docpath, relpath)
    soup = BeautifulSoup(open(filepath).read())
    print(soup.title)

    # signals
    signals = soup.select("section[id=signals] > ul > li > p > strong")
    anchor = '#signals'
    href = relpath + anchor
    for s in signals:
        if s.text != '(' and s.text != ')':
            s.append(dashAnchor(soup, 'Callback', s.text))
            print('indexing callback ', s.text, ' ', href)
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (s.text, 'Callback', href))

    # enums
    enums = soup.select("section[id=enumerations] > p > strong")
    anchor = "#enumerations"
    href = relpath + anchor
    for e in enums:
        print('indexing enum ', e.text, ' ', href)
        e.append(dashAnchor(soup, 'Enum', e.text))
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (e.text, 'Enum', href))

    #properties
    anchor = '#properties'
    href = relpath + anchor
    props = soup.select("section[id=property-descriptions] > ul > li > p > strong")
    for p in props:
        print('indexing property ', p.text, ' ', href)
        p.append(dashAnchor(soup, 'Property', p.text))
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (p.text, 'Property', href))

    #methods
    anchor = '#methods'
    href = relpath + anchor
    methods = soup.select("section[id=method-descriptions] > ul > li > p > strong")
    for m in methods:
        if m.text != '(' and m.text != ')':
            print('indexing method ', m.text, ' ', href)
            m.append(dashAnchor(soup, 'Method', m.text))
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)', (m.text, 'Method', href))

    #remove sidebar
    sidebar = soup.select_one('nav.wy-nav-side')
    if sidebar:
        sidebar.extract()

    with open(filepath, 'w') as out:
        out.write(soup.prettify())



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

