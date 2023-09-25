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


@st.cache_resource(ttl=3600, show_spinner="Fetching onchain data...")
def getDuneData():
  query = QueryBase(
      name="op_txn_stats",
      query_id=3036014,
  )

  dune = DuneClient(os.environ["DUNE_API_KEY"])
  results = dune.refresh_into_dataframe(query)
  return results


@st.cache_resource(ttl=3600, show_spinner="Fetching onchain data...")
def getMedGas():
  query = QueryBase(
      name="med_gas_price_l1",
      query_id=3051281,
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

num_txns = st.number_input("Enter your estimated number of daily transactions",
                           value=10000,
                           placeholder="Type a number...")

run = st.button("PREDICT", type="primary")

if run:
  df = getDuneData()

  st.subheader(
      "Step 1: Pull revenue and cost for a median transaction (past 24h)")
  st.dataframe(df)

  st.subheader("Step 2: Assume % distribution of txn types")
  df['pct_distribution'] = 0
  df.loc[df['tx_type'] == 'eth_transfer',
         'pct_distribution'] = eth_transfer_pct
  df.loc[df['tx_type'] == 'erc20_transfer',
         'pct_distribution'] = erc20_transfer_pct
  df.loc[df['tx_type'] == 'uniswap_trade',
         'pct_distribution'] = uniswap_trade_pct
  df.loc[df['tx_type'] == 'hop_bridge', 'pct_distribution'] = hop_bridge_pct
  st.write("ETH Transfers = 31% of txns")
  st.write("ERC20 Transfers = 19% of txns")
  st.write("Uniswap Trades = 49% of txns")
  st.write("Hop Bridge Out = 1% of txns")

  st.subheader("Step 3: Predict daily revenue for the rollup")
  st.caption("Sum of (txn revenue * number of transactions) for each transaction type")
  daily_rev = num_txns * (df.apply(
      lambda row: row['med_l2_rev'] * row['pct_distribution'], axis=1).sum())
  st.write("Predicted Daily Revenue = " + str(round(daily_rev,3)) + "ETH")

  st.subheader("Step 4: Predict daily cost for the rollup")
  st.caption("Regression Model is used to calculate the Gas used on L1. This is multiplied by the median gas price of the past day.")
  df['daily_l1_gas_used_inbox'] = df.apply(lambda row: regression_model(
      row['med_calldata_bytes'], row['med_l1_gas_used'],
      (num_txns * row['pct_distribution'])),
                                           axis=1)

  med_gas_price = getMedGas()['median_gas_price_gwei'][0]
  daily_cost = (med_gas_price * df['daily_l1_gas_used_inbox'].sum()) / 1e9
  st.write("Predicted Daily Cost = " + str(round(daily_cost,3) + "ETH")

  st.subheader(':blue[Output]')
  st.caption("Predicted Daily Profit = Predicted Daily Revenue - Predicted Daily Cost")
  st.subheader("Predicted Daily Profit = " + str(round((daily_rev - daily_cost),2)) +
               "ETH")
