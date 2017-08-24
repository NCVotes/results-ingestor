from bokeh.models.widgets import Div, Paragraph, TextInput, PreText, Button, DataTable, TableColumn
from bokeh.layouts import layout, widgetbox, row
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
import requests
import sys
import os
from zipfile import ZipFile
import pandas as pd
import glob
import tempfile
from fuzzywuzzy import process as fuzzymatch
import shutil
import csv
from sqlalchemy import create_engine, exc
import sqlalchemy.types as sqltype

# Set up data
database_url='34.204.163.12:5432'
schema=pd.read_csv('schema.csv')
tempdir=""

global df, database
cols=[]

# Helper functions
def delimiter(filename):
    f=open(filename)
    dialect = csv.Sniffer().sniff(f.readline())
    f.close()
    return dialect.delimiter

# Set up page
## Title
div_title=Div(text="<h1>NC Contest Data</h1>", width=900)
par_text=Paragraph(text="", width=900)

## Widgets
username_input=TextInput(value="Username", title="")
password_input=TextInput(value="Password", title="")
login_button=Button(label="Login", button_type='success',width=150)
url_input = TextInput(value="", title="Data file URL:")
fetch_button = Button(label="Fetch", button_type='success',width=150)
progress_bar=PreText(text="",width=900)
ingest_button = Button(label="Ingest", button_type='success',width=150)

## Plot
## Table


# Set up callbacks
def login():
    global database
    database=create_engine('postgresql://{}:{}@{}/ncvoter_prod'.format(username_input.value,password_input.value,database_url))
    try:
        database.connect()
        par_text.text='''Fill in the url of a contest result file and it will be downloaded
        and unzipped if the filename ends with .zip. The data file will be read (only
        csv and tsv files supported) and displayed below with its first 5 rows for preview. Its columns
        will be compared to columns in the schema and possible matches are suggested. Make changes
        as necessay and click Ingest to finish.'''
        widgets.children=widgets.children[:1]
        widgets.children.append(row(widgetbox(url_input,fetch_button)))
        widgets.children.append(row(progress_bar))
    except exc.SQLAlchemyError as err:
        par_text.text=str(err)

login_button.on_click(login)

def download_data():
    global df
    df=None
    fetch_button.disabled=True
    if len(widgets.children)>3:
        widgets.children=widgets.children[:3]
    url=url_input.value
    filename=url.split('/')[-1]
    progress_bar.text='Downloading {}: 0%'.format(filename)
    try:
        resp = requests.get(url, stream=True)
    except requests.exceptions.RequestException as err:
        progress_bar.text=str(err)
        fetch_button.disabled=False
        return 1
    if resp.status_code == 200:
        tempdir=tempfile.mkdtemp(dir='./')
        with open(os.path.join(tempdir,filename), "wb") as f:
            total_length = resp.headers.get('content-length')
            if total_length is None: # no content length header
                f.write(resp.content)
            else:
                dl = 0
                done = 0
                total_length = int(total_length)
                for data in resp.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    if done != int(50 * dl / total_length):
                        done = int(50 * dl / total_length)
                        progress_bar.text='Downloading {}: {}%'.format(filename, done*2)
            progress_bar.text='Downloaded {}'.format(filename)
        if filename.endswith('.zip'):
            progress_bar.text='Unzipping {}'.format(filename)
            with ZipFile(os.path.join(tempdir,filename), "r") as z:
                z.extractall(tempdir)
            progress_bar.text='Unzipped {}'.format(filename)
            os.remove(os.path.join(tempdir,filename))

        dfs=[]
        for infile in glob.glob(os.path.join(tempdir,"*")):
            sep=delimiter(infile)
            dfs.append(pd.read_csv(infile, sep=sep, na_values='Not Found'))
        df=pd.concat(dfs, ignore_index=True)
        columns = [TableColumn(field=i, title=i) for i in df.columns]
        table = DataTable(source=ColumnDataSource(df.head().fillna('.')), columns=columns, width=1200, height=150)
        widgets.children.append(row(table))
        progress_bar.text='Preview {}. {} rows, {} columns'.format(filename, df.shape[0], df.shape[1])

        widgets.children.append(row(Paragraph(text='''Columns that possibly match
        the grand schema are suggested below. Make changes as necessary. Leave the box empty
        if no column in the data file matches that field.''', width=900)))
        del cols[:]
        for i in schema.columns:
            match=fuzzymatch.extractOne(i,df.columns)
            if i == 'candidate' and match[1]<60:
                match=fuzzymatch.extractOne('choice',df.columns)
            if match[1]>60:
                cols.append(widgetbox(Paragraph(text=i+' = '), TextInput(value=match[0], title=""), width=155))
            else:
                cols.append(widgetbox(Paragraph(text=i+' = '), TextInput(value="", title=""), width=155))
        widgets.children.append(row(*cols))
        shutil.rmtree(tempdir)

        widgets.children.append(row(ingest_button))
        ingest_button.label="Ingest"
        ingest_button.disabled=False
        fetch_button.disabled=False
        return 0

    progress_bar.text='Failed to download {}'.format(filename)
    fetch_button.disabled=False
    return 1

fetch_button.on_click(download_data)

def ingest_data():
    global df
    if df is None:
        return
    fetch_button.disabled=True
    ingest_button.disabled=True
    ingest_button.label="Wait"
    colnames=[(i.children[1].value, i.children[0].text.replace('=','').strip()) for i in cols if i.children[1].value]
    colnames=dict(colnames)
    for i in colnames:
        if i not in df.columns:
            if colnames[i]=='election_date':
                df[i]=pd.to_datetime(i)
            else:
                df[i]=i
    df=df[colnames.keys()]
    df.rename(columns=colnames,inplace=True)
    if ("district" not in df.columns) or (not df['district'].any()):
        # district + number
        indx=df['contest_name'].str.contains(r'DISTRICT \d', case=False)
        if indx.any():
            dis=df.loc[indx,'contest_name'].str.upper().str.rsplit(r'DISTRICT',n=1,expand=True)
            df.loc[indx,'contest_name']=dis[0]
            df.loc[indx,'district']=dis[1]
        # district + single letter
        indx=df['contest_name'].str.contains(r'DISTRICT [a-z]\b', case=False)
        if indx.any():
            dis=df.loc[indx,'contest_name'].str.upper().str.rsplit(r'DISTRICT',n=1,expand=True)
            df.loc[indx,'contest_name']=dis[0]
            df.loc[indx,'district']=dis[1]
        # district + roman numeral from 1-9
        indx=df['contest_name'].str.contains(r'DISTRICT (IX|I?V|V?I{1,3})\b', case=False)
        if indx.any():
            dis=df.loc[indx,'contest_name'].str.upper().str.rsplit(r'DISTRICT',n=1,expand=True)
            df.loc[indx,'contest_name']=dis[0]
            df.loc[indx,'district']=dis[1]
    df2=pd.concat([schema,df], axis=0, ignore_index=True)

    # if os.path.isfile(database_url):
    #     with open(database_url,'a') as outfile:
    #         df2.to_csv(outfile, sep='\t', header=False, index=False)
    # else:
    #     with open(database_url,'w') as outfile:
    #         df2.to_csv(outfile, sep='\t', header=True, index=False)
    df2.to_sql("contest_precinct", database, if_exists='append', index=False, dtype={'absentee_by_mail': sqltype.Integer,
     'candidate': sqltype.Text,
     'contest_group_id': sqltype.Text,
     'contest_name': sqltype.Text,
     'contest_type': sqltype.Text,
     'county': sqltype.Text,
     'district': sqltype.Text,
     'election_date': sqltype.Date,
     'election_day': sqltype.Integer,
     'first_name': sqltype.Text,
     'has_primary': sqltype.Boolean,
     'is_partisan': sqltype.Boolean,
     'is_unexpired': sqltype.Boolean,
     'last_name': sqltype.Text,
     'middle_name': sqltype.Text,
     'name_suffix_lbl': sqltype.Text,
     'nick_name': sqltype.Text,
     'one_stop': sqltype.Integer,
     'party_candidate': sqltype.Text,
     'party_contest': sqltype.Text,
     'precinct': sqltype.Text,
     'provisional': sqltype.Integer,
     'term': sqltype.Text,
     'total_votes': sqltype.Integer,
     'vote_for': sqltype.Integer,
     'winner_flag': sqltype.Integer})

    df=None
    ingest_button.label="Done"
    fetch_button.disabled=False
    ingest_button.disabled=False

ingest_button.on_click(ingest_data)

# Set up layouts and add to document
widgets=layout([[widgetbox(div_title, par_text)],
                [widgetbox(username_input,password_input,login_button)]])

curdoc().add_root(widgets)
curdoc().title = "NC Contest"
