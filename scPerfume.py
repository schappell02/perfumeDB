from bs4 import BeautifulSoup
import urllib2
from urllib2 import HTTPError
import re
import copy
import sqlite3
import pickle



def getReviewURL(startURL='https://www.bpal.org/forum/3-reviews/',savePath=None):
    """
    Function to return list of urls of pages with reviews of BPAL's perfumes. Starts with given url and finds all corresponding links on that page.
    Then searches those links for review pages and so on, until review forum is searched. Will either return list or save to file given savePath

    startURL - initial url to begin search and web scraping, general review forum page.

    savePath - optional path of save file
    """

    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(startURL,headers=hdr)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page,'html.parser')

    list_nex = []
    # searches for links that are also within forum
    for tmp in soup.findAll('a',attrs={'href':re.compile('^https://www.bpal.org/forum')}):
        tlink = tmp.get('href')
        # checks that they are not already on list and other checks, before appending to list
        if not tlink.startswith('https://www.bpal.org/forum/47-') and not tlink.startswith('https://www.bpal.org/forum/3-') and tlink not in list_nex:
            list_nex.append(tlink)

    list_rev = []
    # after initial search, search those found pages
    for tmp in list_nex:
        req = urllib2.Request(tmp,headers=hdr)
        page = urllib2.urlopen(req)
        soup = BeautifulSoup(page,'html.parser')
        for link in soup.findAll('a',attrs={'href':re.compile('^https://www.bpal.org/')}):
            tlink = link.get('href')
            # check if this is another page to search for review links
            if tlink.startswith('https://www.bpal.org/forum/') and 'sortby' not in tlink and tlink not in list_nex and not tlink.startswith('https://www.bpal.org/forum/47-') and not tlink.startswith('https://www.bpal.org/forum/3-') and not tlink.endswith('.xml/'):
                list_nex.append(tlink)
            
            # or if it is a review page itself (and check it's not already on list)
            elif tlink.startswith('https://www.bpal.org/topic/') and tlink not in list_rev and not tlink.endswith('Comment') and '/?page=' not in tlink:
                list_rev.append(tlink)

    if savePath != None:
        with open(savePath,'wb') as fp:
            pickle.dump(list_rev,fp)
    else:
        return list_rev




def getScentInfo(scent_url):
    """
    Returns info from url inputted. Assumes it is a review page on BPAL's forum. Returns name of scent, collection, any tags, and description of scent
    """
    hdr = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib2.Request(scent_url,headers=hdr)
        page = urllib2.urlopen(req)
        soup = BeautifulSoup(page,'html.parser')
    
        ret_title = soup.find('meta',attrs={'property':'og:title'})['content']
        tmp_array = re.findall(r'.+? -',soup.title.text)
        ret_colle = tmp_array[1][1:-2]
        # search for tags
        try:
            ret_tags = soup.find('meta',attrs={'name':'keywords'})['content']
        except TypeError:
            ret_tags = ''
        # search for description
        try:
            tmp_str = soup.select('div[style*="background-color:transparent"]')[0].find_all('strong')[-1].text
        except AttributeError:
            tmp_str = soup.select('div[style*="background-color:transparent"]')[0].text
        except IndexError:
            tmp_str = ''
        # only take part of description that mentions notes
        try:
            ret_descr = re.findall(r':.+',tmp_str)[0][2:]
        except IndexError:
            ret_descr = tmp_str
        ret_descr = ret_descr.replace('"',"'")
    
        return ret_title, ret_colle, ret_tags, ret_descr 

    except HTTPError:
        return '','','',''




def queryPerfume(want_notes,death_notes=None):
    """
    Function performs SQL query on already existing database, returns resulting cursor with all information about corresponding scents.

    want_notes - string of single note of interest or list of desired notes. If more than one note is given, query will require scents
    to have all given notes.

    death_notes - if given, individual or list of notes required to not be in perfumes.
    """

    sql_query = "SELECT COUNT(*) FROM bpalmain WHERE"
    if type(want_notes) == str:
        sql_query += " (pdescription LIKE '%"+want_notes+"%'"
    elif type(want_notes) == list:
        sql_query += " pdescription LIKE '%"+want_notes[0]+"%'"
        for i in range(len(want_notes)-1):
            sql_query += " AND pdescription LIKE '%"+want_notes[i+1]+"%'"
    else:
        print('Input want notes needs to be a string or a list of strings')
    
    if death_notes != None:
        if type(death_notes) == str:
            sql_query += " AND pdescription NOT LIKE '%"+death_notes+"%'"
        elif type(death_notes) == list:
            for i in range(len(death_notes)):
                sql_query += " AND pdescription NOT LIKE '%"+death_notes[i]+"%'"
        else:
            print('Death notes needs to a string or a list of strings')
    
    # some perfumes in database are single note, the name of the perfume gives the scent, and their is no provided description
    if type(want_notes) == str:
        sql_query += ") OR (pname LIKE '%"+want_notes+"%' and pcollection LIKE '%single%')"
    
    # so far, function has been constructing the needed SQL query
    to_print = crsr.execute(sql_query)
    for tmp in to_print:
        print(str(tmp[0])+' results found')
    sql_query = "SELECT *"+sql_query[15:]
    return crsr.execute(sql_query)
