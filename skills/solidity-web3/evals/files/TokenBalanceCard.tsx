import { useEffect, useState } from "react";
import { useAccount, useReadContract } from "wagmi";
import { formatUnits } from "viem";

const VAULT_ABI = [
  {
    type: "function",
    name: "balanceOf",
    stateMutability: "view",
    inputs: [{ name: "user", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
  },
] as const;

const VAULT_ADDRESS = "0x0000000000000000000000000000000000000BAD" as const;

type Props = {
  decimals: number;
  onLoaded: (formatted: string) => void;
};

export function TokenBalanceCard({ decimals, onLoaded }: Props) {
  const { address, isConnected } = useAccount();
  const [history, setHistory] = useState<string[]>([]);

  const { data, isLoading, error } = useReadContract({
    abi: VAULT_ABI,
    address: VAULT_ADDRESS,
    functionName: "balanceOf",
    args: [address!],
  });

  const formatted = formatUnits(data ?? 0n, decimals);

  useEffect(() => {
    setHistory([...history, formatted]);
    onLoaded(formatted);
  });

  if (!isConnected) return <p>Connect a wallet</p>;

  return (
    <div className="card">
      <h3>Vault balance</h3>
      <p>{isLoading ? "…" : formatted}</p>
      {error ? <p className="error">{error.message}</p> : null}
      <ul>
        {history.map((h) => (
          <li>{h}</li>
        ))}
      </ul>
    </div>
  );
}
