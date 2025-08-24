// master-ip/contracts/hardhat.config.js
import { config as dotenvConfig } from "dotenv";
import "@nomicfoundation/hardhat-ethers";

dotenvConfig();

export default {
  solidity: "0.8.20",
  networks: {
    amoy: {
      url: process.env.AMOY_RPC || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    sepolia: {
      url: process.env.SEPOLIA_RPC || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  }
};
