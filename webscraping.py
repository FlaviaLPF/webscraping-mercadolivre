import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
from pandasql import sqldf
import csv
from matplotlib import pyplot as plt
import seaborn as sns



#function to perform a request and scrape the page
def scrape_page(url):
  headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
  page = requests.get(url,headers=headers)
  soup = BeautifulSoup(page.text, 'html.parser')
  #wait a few seconds for the browser to load
  time.sleep(2)
  if page.status_code != 200:
    print("It is not possible to load the page: ", page.status_code)
    quit()
  else:
    return soup

#function to save data for all phones of a specific brand
def grava_dados_produtos_da_marca(products):
  cont = 0
  for prod in lista_fones:
    #Extract the name and price of the phone
    name = prod.find('a', {'class': 'poly-component__title'}).get_text()
    price = prod.find('span', {'class': 'andes-money-amount'}).text
    marca = marcas['nome']
    produto = name
    #Format the price and convert it to a numeric value
    preco = price
    preco = preco.replace('R$', '')
    preco = preco.replace('.', '')
    preco = preco.replace(',', '.')
    preco = float(preco)
    #Extract the phone's rating
    if prod.find('span', {'class': 'poly-reviews__rating'}) != None:
      avaliacao = prod.find('span', {'class': 'poly-reviews__rating'}).get_text()
    else:
      avaliacao = '-'
    fone.append([marca,produto,preco,avaliacao])
    cont += 1

#configura dados para acessar página principal
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
url = 'https://lista.mercadolivre.com.br/fone-sem-fio#D[A:fone%20sem%20fio]'

#chamar a funçao scrape_page
soup = scrape_page(url)
Configure data to access the main page
if soup == None:
  print('It is not possible to load the page')
  quit()

#Save from the main page all data for the brand-related filter.
marcas = soup.find_all('div', {'class': 'ui-search-filter-dl'})[3]

#Select all brands within the selections
listas_marcas = marcas.find_all('li',{'class': 'ui-search-filter-container'})

# Save the product brand, the number of results/phones, and the link to access the phones for that brand.
marcas = {}
cont = 0
url = ''
fone = []

#Extract the brand name and the link to the page for a specific brand's phones and store the data in a dictionary.

for item in listas_marcas:
  nome = item.find('span',{'class': 'ui-search-filter-name'}).get_text()
  url = item.find('a',{'class': 'ui-search-link'})['href']
  marcas['nome'] = nome
  marcas['link'] = url
  products = scrape_page(url)
  if products != None:
    lista_fones = products.find_all('li', {'class': 'ui-search-layout__item'})
    grava_dados_produtos_da_marca(lista_fones)
  else:
    print('It was not possible to load the page for brand:', marcas['nome'])
    print('Page status: ', page.status_code)
    quit()

  cont += 1
  #Save up to 8 headphone brands.
  if cont == 8:
    break

# Create a DataFrame with the collected data.
df = pd.DataFrame(fone,columns=['marca','produto','preco','avaliacao'])

# Write data to the CSV file.
uri = 'pesquisa_mercado'
df.to_csv(uri,index='false', sep=',')

#Print descriptive statistics. Calculate values using SQL to find the average price per brand.
query = ''' SELECT marca, AVG(preco) AS media_preco FROM df GROUP BY marca ORDER BY media_preco '''
result = sqldf(query, locals())
print(result)

df_ordenado1 = df.loc[df['marca'] == 'Genérica']
print('genérica')
df_ordenado1.describe()

df_ordenado2 = df.loc[df['marca'] == 'Kaidi']
print('kaidi')
df_ordenado2.describe()

df_ordenado2 = df.loc[df['marca'] == 'TWS']
print('tws')
df_ordenado2.describe()

#Print descriptive statistics. Calculate values using SQL to find the minimum and maximum price per brand.
query = ''' SELECT marca, MIN(preco) AS valor_minimo, MAX(preco) AS valor_maximo FROM df GROUP BY marca  ORDER BY valor_minimo '''

result = sqldf(query, locals())
print(result)

#Calculate the median of each price variation for each brand.
query = ''' WITH ordenado AS (
    SELECT
        marca,
        preco,
        ROW_NUMBER() OVER (PARTITION BY marca ORDER BY preco) AS rn,
        COUNT(*) OVER (PARTITION BY marca) AS cnt
    FROM
        df
),
mediana AS (
    SELECT
        marca,
        preco,
        CASE
            WHEN cnt % 2 = 1 AND rn = (cnt / 2) + 1 THEN preco
            WHEN cnt % 2 = 0 AND rn IN ((cnt / 2), (cnt / 2) + 1) THEN preco
        END AS mediana_valor
    FROM
        ordenado
)
SELECT
    marca,
    AVG(mediana_valor) AS mediana_preco
FROM
    mediana
WHERE
    mediana_valor IS NOT NULL
GROUP BY
    marca ORDER BY preco '''

result = sqldf(query, locals())
print(result)

#Calculate using SQL to find the minimum rating for each brand and the product that received that rating.
query =  ''' SELECT marca, avaliacao,produto FROM df WHERE avaliacao = (SELECT MIN(avaliacao) FROM df v2 WHERE v2.marca = df.marca AND
v2.avaliacao <> '-') GROUP BY marca,avaliacao,produto ORDER BY avaliacao '''

result_avalia = sqldf(query, locals())
print(result_avalia)

# Calculate the average rating for each brand.
query = ''' SELECT marca, AVG(avaliacao) AS media_avaliacao FROM df  WHERE avaliacao <> '-' GROUP BY marca ORDER BY media_avaliacao '''

result_avalia = sqldf(query, locals())
print(result_avalia)

#Price values frequency chart
df['preco'].plot(kind='hist', bins=20, title='Gráfico de Distribuição - preços')
plt.gca().spines[['top', 'right',]].set_visible(False)

#Violin distribution chart
df['preco'].plot(kind='line', figsize=(8, 4), title='Gráfico de Valores')
plt.gca().spines[['top', 'right']].set_visible(False)


#Violin distribution chart
figsize = (12, 1.2 * len(df['marca'].unique()))
plt.figure(figsize=figsize)
sns.violinplot(df, x='preco', y='marca', inner='stick', palette='Dark2')
sns.despine(top=True, right=True, bottom=True, left=True)