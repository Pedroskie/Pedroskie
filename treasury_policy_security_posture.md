# Treasury Policy Security Posture

## Overview
This brief describes the current treasury security configuration, focusing on how the hot wallet allocation, minimum confirmation settings, and Layer 2 (L2) environment shape the overall risk profile.

- **Governance Mechanism:** 2-of-3 Safe multisig controls treasury disbursements.
- **Hot Wallet Cap:** 20% of total assets are maintained in the hot wallet.
- **Settlement Assurance:** Incoming transfers on Base require 6 block confirmations before funds are considered finalized.

## Strengths
- The 2-of-3 Safe multisig distributes authority across multiple signers, mitigating the risk of a single compromised key triggering large transfers.
- Restricting the hot wallet to 20% of assets offers liquidity for daily operations while limiting the potential loss exposure in the event of a hot wallet breach.
- Requiring six block confirmations on Base balances operational speed with protection against chain reorganizations, reducing the likelihood of double-spend attacks impacting treasury inflows.

## Residual Risks
- **Signer Coordination:** Multisig effectiveness depends on active, security-conscious signers. Delays or compromised signers could still impede or threaten treasury operations.
- **Hot Wallet Exposure:** Although capped, the hot wallet remains internet-connected and attractive to attackers; security monitoring and rapid incident response are essential.
- **L2 Dependency:** Relying on Base inherits its consensus and bridge security properties; upstream issues or prolonged sequencer downtime may delay withdrawals or confirmations.

## Recommendations
1. **Enhance Operational Resilience:** Establish emergency procedures and signer rotation policies to address key compromise or unavailability scenarios.
2. **Continuous Monitoring:** Implement real-time alerts for large hot wallet movements and periodic security reviews of signer devices.
3. **Bridge Contingency Planning:** Prepare fallback liquidity strategies for potential Base outages or bridge congestion, ensuring critical treasury operations can continue.

By maintaining strong governance, limiting hot wallet exposure, and planning for L2 contingencies, the treasury can uphold a balanced security posture while meeting operational needs.
