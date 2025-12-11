// functions/alerts/slackRelayEnhanced.js
import { onMessagePublished } from "firebase-functions/v2/pubsub";
import fetch from "node-fetch";
import { SecretManagerServiceClient } from "@google-cloud/secret-manager";

const secretClient = new SecretManagerServiceClient();

/**
 * Gemini Cloud Enhanced Slack Relay
 * ---------------------------------
 * - Subscribes to Pub/Sub topic: heartbeat-alerts-topic
 * - Retrieves webhook from Secret Manager (SLACK_ALERT_WEBHOOK)
 * - Parses alert payload and sends styled message to Slack
 * - Threads repeated alerts by policy ID
 */
export const slackRelayEnhanced = onMessagePublished(
  "heartbeat-alerts-topic",
  async (event) => {
    try {
      const rawData = Buffer.from(event.data.message.data, "base64").toString();
      console.log("📩 Incoming alert:", rawData);

      // 1️⃣ Load Slack webhook from Secret Manager
      const [version] = await secretClient.accessSecretVersion({
        name: `projects/${process.env.GCLOUD_PROJECT}/secrets/SLACK_ALERT_WEBHOOK/versions/latest`,
      });
      const webhookUrl = version.payload.data.toString();

      // 2️⃣ Parse message
      let payload;
      try {
        payload = JSON.parse(rawData);
      } catch {
        payload = { text: rawData };
      }

      const alertTitle =
        payload.policyName ||
        payload.title ||
        "Gemini Cloud Heartbeat Alert ⚠️";

      const message =
        payload.text ||
        payload.message ||
        payload.body ||
        "An unspecified alert was received from Gemini Cloud.";

      const severity =
        payload.severity?.toLowerCase() || payload.status?.toLowerCase() || "warning";

      // 3️⃣ Determine Slack color
      const color =
        severity.includes("ok") || severity.includes("resolved")
          ? "#36A64F" // Green
          : severity.includes("critical") || severity.includes("error")
          ? "#FF0000" // Red
          : "#FFCC00"; // Yellow

      // 4️⃣ Format message blocks
      const blocks = [
        {
          type: "header",
          text: { type: "plain_text", text: `🧠 ${alertTitle}`, emoji: true },
        },
        {
          type: "section",
          text: { type: "mrkdwn", text: message },
        },
      ];

      if (payload.link || payload.url) {
        blocks.push({
          type: "actions",
          elements: [
            {
              type: "button",
              text: { type: "plain_text", text: "Open in Console", emoji: true },
              url: payload.link || payload.url,
              style: "primary",
            },
          ],
        });
      }

      // 5️⃣ Thread key (so alerts from same policy group together)
      const threadKey = payload.policyId || payload.policy_name || "heartbeat-core";
      const threadTs = Buffer.from(threadKey).toString("base64").slice(0, 10);

      const slackPayload = {
        attachments: [
          {
            color,
            blocks,
          },
        ],
        // Slack threading hint: use the same ts for recurring alerts
        thread_ts: threadTs,
      };

      // 6️⃣ Send to Slack
      const res = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(slackPayload),
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`Slack responded ${res.status}: ${body}`);
      }

      console.log(`✅ Alert posted to Slack (${severity.toUpperCase()}).`);
    } catch (err) {
      console.error("❌ Enhanced Slack Relay failed:", err);
    }
  }
);
