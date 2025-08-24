// master-ip/contracts/scripts/deploy.js
export default async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  const Factory = await ethers.getContractFactory("AnchorRegistry");
  const c = await Factory.deploy();
  await c.waitForDeployment();

  console.log("AnchorRegistry deployed to:", await c.getAddress());
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
