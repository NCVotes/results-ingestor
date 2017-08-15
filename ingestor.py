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

# Set up data
database_url='fakebase.tsv'
schema=pd.read_csv('schema.csv')
tempdir=""

global df
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
par_text=Paragraph(text='''Fill in the url of the file and it will be downloaded
and unzipped if the filename ends with .zip. The data file will be read (only support
csv and tsv formats) and displayed below with its first 5 rows for preview. Its columns
will be compared to columns in the schema and possible matches are suggested. Make changes
as necessay and click Ingest to finish.''', width=900)

## Widgets
text_input = TextInput(value="", title="Data file URL:")
button = Button(label="Fetch", button_type='success',width=150)
progress_bar=PreText(text="",width=900)
button_ingest = Button(label="Ingest", button_type='success',width=150)

## Plot
## Table


# Set up callbacks
def download_data():
    global df

    if len(widgets.children)>3:
        widgets.children=widgets.children[:3]
    url=text_input.value
    filename=url.split('/')[-1]
    progress_bar.text='Downloading {}: 0%'.format(filename)
    resp = requests.get(url, stream=True)
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

        df=None
        dfs=[]
        for infile in glob.glob(os.path.join(tempdir,"*")):
            sep=delimiter(infile)
            dfs.append(pd.read_csv(infile, sep=sep))
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
            if match[1]>60:
                cols.append(widgetbox(Paragraph(text=i+' = '), TextInput(value=match[0], title=""), width=155))
            else:
                cols.append(widgetbox(Paragraph(text=i+' = '), TextInput(value="", title=""), width=155))
        widgets.children.append(row(*cols))
        shutil.rmtree(tempdir)

        widgets.children.append(row(button_ingest))
        button_ingest.label="Ingest"
        return 0

    progress_bar.text='Failed to download {}'.format(filename)
    return 1

button.on_click(download_data)

def ingest_data():
    global df
    if df==None:
        return
    button_ingest.label="Wait"
    colnames=[(i.children[1].value, i.children[0].text.replace('=','').strip()) for i in cols if i.children[1].value]
    colnames=dict(colnames)
    df=df[colnames.keys()]
    df.rename(columns=colnames,inplace=True)
    df2=pd.concat([schema,df], axis=0, ignore_index=True)
    print(df2.head())

    if os.path.isfile(database_url):
        with open(database_url,'a') as outfile:
            df2.to_csv(outfile, sep='\t', header=False, index=False)
    else:
        with open(database_url,'w') as outfile:
            df2.to_csv(outfile, sep='\t', header=True, index=False)

    df=None
    button_ingest.label="Done"

button_ingest.on_click(ingest_data)

# Set up layouts and add to document
widgets=layout([[widgetbox(div_title, par_text)],
                [widgetbox(text_input,button)],
                [progress_bar]])

curdoc().add_root(widgets)
curdoc().title = "NC Contest"
