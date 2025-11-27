#!/usr/bin/env node
/**
 * Notification Hook
 * Routes notifications to various channels
 * - Slack, Discord, Teams
 * - Email, webhooks
 * - PagerDuty (for critical events)
 */

const https = require('https');
const { URL } = require('url');

function sendWebhook(url, payload) {
  return new Promise((resolve, reject) => {
    try {
      const parsedUrl = new URL(url);
      const data = JSON.stringify(payload);

      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || 443,
        path: parsedUrl.pathname + parsedUrl.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': data.length
        }
      };

      const req = https.request(options, (res) => {
        let responseData = '';
        res.on('data', (chunk) => responseData += chunk);
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(responseData);
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${responseData}`));
          }
        });
      });

      req.on('error', reject);
      req.write(data);
      req.end();

    } catch (err) {
      reject(err);
    }
  });
}

function main() {
  try {
    const args = process.argv.slice(2);
    const notification = args[0] ? JSON.parse(args[0]) : {};

    const message = notification.message || 'Claude Code notification';
    const level = notification.level || 'info';

    console.log(`📢 Notification (${level}): ${message}`);

    // Check for webhook URLs in environment
    const slackWebhook = process.env.SLACK_WEBHOOK_URL;
    const discordWebhook = process.env.DISCORD_WEBHOOK_URL;
    const teamsWebhook = process.env.TEAMS_WEBHOOK_URL;
    const customWebhook = process.env.OMNIAUDIT_WEBHOOK_URL;

    const promises = [];

    // Send to Slack
    if (slackWebhook) {
      const slackPayload = {
        text: message,
        blocks: [
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `*OmniAudit Notification*\n${message}`
            }
          }
        ]
      };

      promises.push(
        sendWebhook(slackWebhook, slackPayload)
          .then(() => console.log('  ✓ Sent to Slack'))
          .catch(err => console.warn('  ⚠️  Slack webhook failed:', err.message))
      );
    }

    // Send to Discord
    if (discordWebhook) {
      const discordPayload = {
        content: message,
        embeds: [
          {
            title: 'OmniAudit Notification',
            description: message,
            color: level === 'error' ? 0xff0000 : level === 'warn' ? 0xffa500 : 0x00ff00,
            timestamp: new Date().toISOString()
          }
        ]
      };

      promises.push(
        sendWebhook(discordWebhook, discordPayload)
          .then(() => console.log('  ✓ Sent to Discord'))
          .catch(err => console.warn('  ⚠️  Discord webhook failed:', err.message))
      );
    }

    // Send to custom webhook
    if (customWebhook) {
      const customPayload = {
        message,
        level,
        timestamp: new Date().toISOString(),
        source: 'omniaudit-claude-code'
      };

      promises.push(
        sendWebhook(customWebhook, customPayload)
          .then(() => console.log('  ✓ Sent to custom webhook'))
          .catch(err => console.warn('  ⚠️  Custom webhook failed:', err.message))
      );
    }

    // Wait for all notifications to complete
    Promise.allSettled(promises).then(() => {
      if (promises.length === 0) {
        console.log('  ℹ️  No webhook URLs configured (set SLACK_WEBHOOK_URL, etc.)');
      }
      console.log('✅ Notification processing completed');
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ Notification hook error:', error.message);
    process.exit(0);
  }
}

main();
