const fs = require("fs");
const path = require("path");
const solc = require("solc");

function loadSource(rel) {
  return fs.readFileSync(path.join(__dirname, "..", "contracts", rel), "utf8");
}

const sources = {
  "PolicyVault.sol": { content: loadSource("PolicyVault.sol") },
  "mocks/MockERC20.sol": { content: loadSource("mocks/MockERC20.sol") },
  "mocks/MockAavePool.sol": { content: loadSource("mocks/MockAavePool.sol") },
};

const input = {
  language: "Solidity",
  sources,
  settings: {
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
    optimizer: { enabled: true, runs: 200 },
  },
};

const output = JSON.parse(solc.compile(JSON.stringify(input)));

if (output.errors) {
  let hasError = false;
  for (const err of output.errors) {
    console.log(err.severity.toUpperCase() + ":", err.formattedMessage);
    if (err.severity === "error") hasError = true;
  }
  if (hasError) process.exit(1);
}

const result = {};
for (const [file, contracts] of Object.entries(output.contracts)) {
  for (const [name, data] of Object.entries(contracts)) {
    result[name] = {
      abi: data.abi,
      bytecode: "0x" + data.evm.bytecode.object,
    };
  }
}

fs.writeFileSync(path.join(__dirname, "..", "compiled.json"), JSON.stringify(result, null, 2));
console.log("Compiled contracts:", Object.keys(result).join(", "));
