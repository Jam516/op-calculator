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

eth_transfer_pct = 0.31
erc20_transfer_pct = 0.19
uniswap_trade_pct = 0.49
hop_bridge_pct = 0.01

@st.cache_resource(ttl=3600, show_spinner="Fetching data from API...")
def getDuneData():
  query = QueryBase(
      name="op_txn_stats",
      query_id=3036014,
  )

  dune = DuneClient(os.environ["DUNE_API_KEY"])
  results = dune.refresh_into_dataframe(query)
  return results


def regression_model(calldata_bytes_per_user_tx, calldata_gas_per_user_tx,
                     l2_num_txs_per_day):
  # Coefficients
  intercept = 36072092.42860007
  coef_calldata_bytes_per_user_tx = -3716.8613013091917
  coef_calldata_gas_per_user_tx = 91.97592357479029
  coef_l2_num_txs_per_day = 1326.8156406251255
  coef_calldata_bytes_per_user_tx2 = 12.794672518158018
  coef_calldata_bytes_per_user_tx_calldata_gas_per_user_tx = -2.093033664012317
  coef_calldata_bytes_per_user_tx_l2_num_txs_per_day = -6.322923102546262
  coef_calldata_gas_per_user_tx2 = 0.08588471077448556
  coef_calldata_gas_per_user_tx_l2_num_txs_per_day = 1.3786867756176369
  coef_l2_num_txs_per_day2 = -0.00023124255145035022

  # Regression model equation
  result = (intercept +
            coef_calldata_bytes_per_user_tx * calldata_bytes_per_user_tx +
            coef_calldata_gas_per_user_tx * calldata_gas_per_user_tx +
            coef_l2_num_txs_per_day * l2_num_txs_per_day +
            coef_calldata_bytes_per_user_tx2 * calldata_bytes_per_user_tx**2 +
            coef_calldata_bytes_per_user_tx_calldata_gas_per_user_tx *
            calldata_bytes_per_user_tx * calldata_gas_per_user_tx +
            coef_calldata_bytes_per_user_tx_l2_num_txs_per_day *
            calldata_bytes_per_user_tx * l2_num_txs_per_day +
            coef_calldata_gas_per_user_tx2 * calldata_gas_per_user_tx**2 +
            coef_calldata_gas_per_user_tx_l2_num_txs_per_day *
            calldata_gas_per_user_tx * l2_num_txs_per_day +
            coef_l2_num_txs_per_day2 * l2_num_txs_per_day**2)

  return result


#--------------------------------------------------------#
# Main Body
#--------------------------------------------------------#

# Create the title at the top of page
st.title('OP Calculator 🔴✨')
st.subheader('Estimate the profitability of a new OP stack rollup')

num_txns = st.number_input("Enter your estimated number of daily transactions", value=10000, placeholder="Type a number...")

run = st.button("PREDICT", type="primary")

if run:
  df = getDuneData()

  st.subheader("Step 1: Pull revenue and cost for a median transaction (past 24h)")
  st.dataframe(df)
  
  st.subheader("Step 2: Assume % distribution of txn types")
  st.write("ETH Transfers = 31% of txns")
  st.write("ERC20 Transfers = 19% of txns")
  st.write("Uniswap Trades = 49% of txns")
  st.write("Hop Bridge Out = 1% of txns")

  st.subheader("Step 3: Predict daily revenue for the rollup")
  st.caption("Predicted Daily Revenue = number of txn * SUM(txn revenue * pct distrib) ")
  daily_rev = num_txns * (
    eth_transfer_pct * df.loc[df['tx_type'] == 'eth_transfer', 'med_l2_rev'].values[0] 
   + erc20_transfer_pct * df.loc[df['tx_type'] == 'erc20_transfer', 'med_l2_rev'].values[0] 
   + uniswap_trade_pct * df.loc[df['tx_type'] == 'uniswap_trade', 'med_l2_rev'].values[0] 
   + hop_bridge_pct * df.loc[df['tx_type'] == 'hop_bridge', 'med_l2_rev'].values[0] 
  )
  st.write("Predicted Daily Revenue = " + daily_rev + "ETH")

  st.subheader("Step 3: Predict daily cost for the rollup")
  

# with st.form("my_form"):
#   text = st.text_area("Enter a question about Safe protocol:")
#   submitted = st.form_submit_button("Submit")
#   if submitted:
#     print('yaya')

# kdf = getDuneData()
# kdf
