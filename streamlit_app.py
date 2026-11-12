import streamlit as st
import requests  
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
# Convertir a pandas para que el multiselect funcione fuera de Snowflake
fruits = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruits['FRUIT_NAME'].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = ' '
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen +''
        st.subheader(fruit_chosen + 'Nutrition information')
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + fruit_chosen)  
        sf_df=st.dataframe(data=smoothiefroot_response.json(),use_container_width=True)
        

    if st.button('Submit order'):
        # Parámetros (?) en lugar de concatenar texto, para evitar errores con comillas
        session.sql(
            "insert into smoothies.public.orders(ingredients, name_on_order) values (?, ?)",
            params=[ingredients_string, name_on_order]
        ).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
else:
    st.write('You have not chosen anything yet')


