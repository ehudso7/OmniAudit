import PropTypes from 'prop-types';

function Pricing({ onSelectPlan }) {
  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: 0,
      period: 'forever',
      description: 'For individual developers',
      features: [
        '1 repository',
        '50 PR reviews/month',
        'Basic security scanning',
        'Community support',
      ],
      limitations: ['No team features', 'Limited AI insights'],
      cta: 'Get Started',
      popular: false,
    },
    {
      id: 'pro',
      name: 'Pro',
      price: 19,
      period: 'per user/month',
      description: 'For professional developers',
      features: [
        'Unlimited repositories',
        'Unlimited PR reviews',
        'Advanced security scanning',
        'Performance analysis',
        'Custom rules',
        'Priority support',
        'API access',
      ],
      limitations: [],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      id: 'team',
      name: 'Team',
      price: 39,
      period: 'per user/month',
      description: 'For development teams',
      features: [
        'Everything in Pro',
        'Team dashboard',
        'Code owner integration',
        'Slack/Teams integration',
        'Custom webhooks',
        'Analytics & reporting',
        'SLA guarantee',
      ],
      limitations: [],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: null,
      period: 'custom',
      description: 'For large organizations',
      features: [
        'Everything in Team',
        'SSO/SAML',
        'Self-hosted option',
        'Custom AI models',
        'Compliance reports (SOC2, HIPAA)',
        'Dedicated support',
        'On-premise deployment',
        'Custom integrations',
      ],
      limitations: [],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  return (
    <div className='pricing'>
      <div className='pricing-header'>
        <h2>Simple, Transparent Pricing</h2>
        <p>Start free, scale as you grow. No hidden fees.</p>
      </div>

      <div className='pricing-grid'>
        {plans.map((plan) => (
          <div key={plan.id} className={`pricing-card ${plan.popular ? 'popular' : ''}`}>
            {plan.popular && <div className='popular-badge'>Most Popular</div>}
            <div className='plan-header'>
              <h3>{plan.name}</h3>
              <p className='plan-description'>{plan.description}</p>
              <div className='plan-price'>
                {plan.price !== null ? (
                  <>
                    <span className='price-amount'>${plan.price}</span>
                    <span className='price-period'>/{plan.period}</span>
                  </>
                ) : (
                  <span className='price-custom'>Custom</span>
                )}
              </div>
            </div>

            <ul className='plan-features'>
              {plan.features.map((feature, idx) => (
                <li key={idx}>
                  <span className='feature-check'>✓</span>
                  {feature}
                </li>
              ))}
              {plan.limitations.map((limitation, idx) => (
                <li key={`limit-${idx}`} className='limitation'>
                  <span className='feature-x'>✗</span>
                  {limitation}
                </li>
              ))}
            </ul>

            <button
              type='button'
              className={`btn ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => onSelectPlan?.(plan.id)}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>

      <div className='pricing-faq'>
        <h3>Frequently Asked Questions</h3>
        <div className='faq-grid'>
          <div className='faq-item'>
            <h4>How does the free trial work?</h4>
            <p>
              Start with a 14-day free trial of Pro or Team. No credit card required. Cancel anytime.
            </p>
          </div>
          <div className='faq-item'>
            <h4>What counts as a PR review?</h4>
            <p>
              Each pull request that OmniAudit analyzes counts as one review, regardless of the number
              of comments.
            </p>
          </div>
          <div className='faq-item'>
            <h4>Can I change plans later?</h4>
            <p>Yes, you can upgrade or downgrade at any time. Changes take effect immediately.</p>
          </div>
          <div className='faq-item'>
            <h4>Do you offer discounts?</h4>
            <p>
              We offer 20% off for annual billing and special pricing for startups and open-source
              projects.
            </p>
          </div>
        </div>
      </div>

      <div className='enterprise-cta'>
        <h3>Need a custom solution?</h3>
        <p>
          Contact our sales team for enterprise pricing, custom integrations, and dedicated support.
        </p>
        <button type='button' className='btn btn-outline'>
          Contact Sales
        </button>
      </div>
    </div>
  );
}

Pricing.propTypes = {
  onSelectPlan: PropTypes.func,
};

export default Pricing;
