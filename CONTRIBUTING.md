# Contributing to OmniAudit

Thank you for your interest in contributing to OmniAudit! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites

- Node.js 20.x or higher
- Git
- Familiarity with TypeScript and React
- An Anthropic API key for testing

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/OmniAudit.git
cd OmniAudit

# Install dependencies
npm install
cd frontend && npm install && cd ..

# Copy environment template
cp .env.example .env

# Add your API keys to .env
```

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run TypeScript compiler
npm run build

# Run type checking
npm run type-check

# Run linter
npm run lint

# Test locally
cd frontend && npm run dev
```

### 4. Commit Your Changes

We follow conventional commits:

```bash
git commit -m "feat: add new skill for dependency analysis"
git commit -m "fix: resolve CORS issue in analyze endpoint"
git commit -m "docs: update API documentation"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Detailed description of what and why
- Screenshots if UI changes
- Reference any related issues

## 🎯 Areas for Contribution

### High Priority

- [ ] Additional language support (Python, Java, Go, Rust)
- [ ] More built-in skills (accessibility, i18n, etc.)
- [ ] Improved error handling and user feedback
- [ ] Performance optimizations
- [ ] Test coverage improvements

### Medium Priority

- [ ] UI/UX enhancements
- [ ] Documentation improvements
- [ ] Example projects and tutorials
- [ ] CI/CD improvements

### Good First Issues

Look for issues labeled `good-first-issue` in the GitHub repository.

## 📝 Code Style Guidelines

### TypeScript

```typescript
// Use explicit types
export interface SkillConfig {
  id: string;
  name: string;
  enabled: boolean;
}

// Use async/await over promises
async function analyzeCode(code: string): Promise<AnalysisResult> {
  const result = await engine.analyze(code);
  return result;
}

// Use const for immutable values
const MAX_RETRIES = 3;
```

### React

```jsx
// Use functional components
function MyComponent({ prop1, prop2 }) {
  const [state, setState] = useState(initial);

  useEffect(() => {
    // Effects here
  }, [dependencies]);

  return <div>...</div>;
}

// Add PropTypes or TypeScript types
MyComponent.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
};
```

## 🧪 Testing Guidelines

### Unit Tests

```typescript
describe('SkillsEngine', () => {
  it('should execute skill successfully', async () => {
    const engine = new SkillsEngine(config);
    const result = await engine.executeSkill('code-quality', input);
    expect(result.success).toBe(true);
  });
});
```

### Integration Tests

Test complete workflows end-to-end.

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Step-by-step instructions
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Node version, browser
6. **Screenshots**: If applicable

## 💡 Suggesting Features

When suggesting features:

1. **Use Case**: Describe the problem it solves
2. **Proposed Solution**: How should it work
3. **Alternatives**: Other approaches considered
4. **Additional Context**: Mockups, examples, etc.

## 📚 Documentation

- Update README.md for new features
- Add JSDoc comments to functions
- Update API documentation
- Include examples in docs/

## ✅ Pull Request Checklist

Before submitting:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Commit messages follow conventional commits
- [ ] Branch is up to date with main
- [ ] No console.log or debugging code
- [ ] Added tests for new features

## 🔍 Code Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, PR will be merged
4. Your contribution will be in the next release!

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙋 Questions?

- Open a discussion on GitHub
- Email: dev@omniaudit.dev

Thank you for contributing to OmniAudit! 🎉
