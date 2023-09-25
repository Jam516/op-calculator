#--------------------------------------------------------#
# Imports
#--------------------------------------------------------#

from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase
import os
import json
import streamlit as st

#--------------------------------------------------------#
# Page Config
#--------------------------------------------------------#

st.set_page_config(
    page_title="OP Calculator",
    page_icon="🔴✨",
    layout="wide",
)

#--------------------------------------------------------#
# Functions
#--------------------------------------------------------#


def getDuneData():
  query = QueryBase(
      name="op_txn_stats",
      query_id=3036014,
  )

  dune = DuneClient(os.environ["DUNE_API_KEY"])
  results = dune.refresh_into_dataframe(query)
  return results


#--------------------------------------------------------#
# Main Body
#--------------------------------------------------------#

# Create the title at the top of page
st.title('OP Calculator 🔴✨')
st.subheader('Estimate the profitability of a new OP stack rollup')

# with st.form("my_form"):
#   text = st.text_area("Enter a question about Safe protocol:")
#   submitted = st.form_submit_button("Submit")
#   if submitted:
#     print('yaya')

kdf = getDuneData()
kdf
