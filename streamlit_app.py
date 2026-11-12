import streamlit as st
import requests  
import pandas as pd
from snowflake.snowpark.functions import col
from cryptography.hazmat.primitives import serialization

cfg = dict(st.secrets["connections"]["snowflake"])
pem = cfg.pop("private_key_pem").encode()
pkey_der = serialization.load_pem_private_key(pem, password=None).private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on smoothie')
st.write('The name on your smoothie will be:', name_on_order)

cnx = st.connection("snowflake", private_key=pkey_der, **cfg)
session = cnx.session()

# Obtener los datos como pandas DataFrame
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON')).to_pandas()
pd_df = my_dataframe

# CORRECCIÓN 1: Pasar únicamente la columna de nombres de frutas al multiselect
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe['FRUIT_NAME'],
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Obtener el valor de SEARCH_ON de forma segura
        search_result = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON']
        search_on = search_result.iloc[0] if not search_result.empty else fruit_chosen
        
        st.subheader(fruit_chosen + ' Nutrition information')
        
        # CORRECCIÓN 2 y 3: Consumir la API de forma segura validando la respuesta
        try:
            smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
            
            if smoothiefroot_response.status_code == 200:
                # Convertir la respuesta JSON a un DataFrame de Pandas para mostrarla limpia
                sf_df = pd.DataFrame([smoothiefroot_response.json()])
                st.dataframe(data=sf_df, use_container_width=True)
            else:
                st.warning(f"No nutrition information available for {fruit_chosen}.")
        except Exception as e:
            st.error(f"Could not fetch data for {fruit_chosen}.")

    if st.button('Submit order'):
        # Uso de parámetros para evitar errores de sintaxis o inyección SQL
        session.sql(
            "insert into smoothies.public.orders(ingredients, name_on_order) values (?, ?)",
            params=[ingredients_string.strip(), name_on_order]
        ).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
else:
    st.write('You have not chosen anything yet')
