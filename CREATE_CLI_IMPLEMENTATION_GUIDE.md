# Implementation Guide: `npx create-veloflow-service`

This guide explains how to create a CLI tool that allows developers to scaffold new VeloFlow services with a single command.

## Architecture Overview

```
npx create-veloflow-service my-pdf-service
  ↓
1. Download create-veloflow-service package from npm
2. Run CLI script
3. Prompt user for configuration
4. Clone/copy service-template
5. Replace all placeholders with user inputs
6. Initialize git repository
7. Install dependencies
8. Display next steps
  ↓
✅ New service ready at ./my-pdf-service/
```

## Project Structure

```
create-veloflow-service/
├── package.json                 # npm package configuration
├── bin/
│   └── create-veloflow-service  # Main CLI entry point
├── src/
│   ├── index.js                 # Main logic
│   ├── prompts.js               # Interactive prompts
│   ├── template.js              # Template file processing
│   ├── git.js                   # Git operations
│   └── utils.js                 # Utility functions
├── templates/                   # (or fetch from GitHub)
│   └── [service-template files]
└── README.md
```

## Step-by-Step Implementation

### Step 1: Create New npm Package

```bash
mkdir create-veloflow-service
cd create-veloflow-service
npm init
```

### Step 2: package.json Configuration

```json
{
  "name": "create-veloflow-service",
  "version": "1.0.0",
  "description": "CLI tool to create new VeloFlow Lambda services",
  "bin": {
    "create-veloflow-service": "./bin/create-veloflow-service"
  },
  "scripts": {
    "test": "jest",
    "lint": "eslint ."
  },
  "keywords": [
    "veloflow",
    "lambda",
    "aws",
    "serverless",
    "scaffold",
    "cli"
  ],
  "author": "VeloQuote",
  "license": "MIT",
  "dependencies": {
    "chalk": "^5.3.0",
    "commander": "^11.1.0",
    "inquirer": "^9.2.12",
    "ora": "^7.0.1",
    "fs-extra": "^11.2.0",
    "degit": "^2.8.4",
    "validate-npm-package-name": "^5.0.0"
  },
  "devDependencies": {
    "eslint": "^8.55.0",
    "jest": "^29.7.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### Step 3: CLI Entry Point

**`bin/create-veloflow-service`** (make executable with `chmod +x`):

```javascript
#!/usr/bin/env node

require('../src/index.js');
```

### Step 4: Main CLI Logic

**`src/index.js`**:

```javascript
const { program } = require('commander');
const chalk = require('chalk');
const inquirer = require('inquirer');
const ora = require('ora');
const path = require('path');
const fs = require('fs-extra');
const { prompts, validateServiceName } = require('./prompts');
const { processTemplate } = require('./template');
const { initGit, createInitialCommit } = require('./git');
const { installDependencies } = require('./utils');

const TEMPLATE_REPO = 'VeloQuote/service-template';

async function main() {
  program
    .name('create-veloflow-service')
    .description('Create a new VeloFlow Lambda service')
    .argument('[service-name]', 'Name of the service to create')
    .option('-t, --template <url>', 'Custom template repository')
    .option('--skip-install', 'Skip dependency installation')
    .option('--skip-git', 'Skip git initialization')
    .parse(process.argv);

  const options = program.opts();
  let serviceName = program.args[0];

  // Welcome message
  console.log();
  console.log(chalk.bold.cyan('🚀 VeloFlow Service Generator'));
  console.log(chalk.gray('   Create production-ready Lambda services'));
  console.log();

  // Get service name if not provided
  if (!serviceName) {
    const { name } = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Service name:',
        validate: validateServiceName,
      },
    ]);
    serviceName = name;
  } else {
    const validation = validateServiceName(serviceName);
    if (validation !== true) {
      console.error(chalk.red(`Error: ${validation}`));
      process.exit(1);
    }
  }

  const targetDir = path.resolve(process.cwd(), serviceName);

  // Check if directory already exists
  if (fs.existsSync(targetDir)) {
    console.error(chalk.red(`Error: Directory "${serviceName}" already exists`));
    process.exit(1);
  }

  // Prompt for service configuration
  console.log();
  console.log(chalk.bold('Service Configuration'));
  console.log(chalk.gray('Answer a few questions to customize your service:\n'));

  const config = await inquirer.prompt(prompts);

  // Download template
  const spinner = ora('Downloading service template...').start();
  try {
    const degit = require('degit');
    const emitter = degit(options.template || TEMPLATE_REPO, {
      cache: false,
      force: true,
    });

    await emitter.clone(targetDir);
    spinner.succeed('Template downloaded');
  } catch (error) {
    spinner.fail('Failed to download template');
    console.error(chalk.red(error.message));
    process.exit(1);
  }

  // Process template files
  spinner.start('Customizing template...');
  try {
    await processTemplate(targetDir, {
      serviceName,
      ...config,
    });
    spinner.succeed('Template customized');
  } catch (error) {
    spinner.fail('Failed to customize template');
    console.error(chalk.red(error.message));
    process.exit(1);
  }

  // Initialize git
  if (!options.skipGit) {
    spinner.start('Initializing git repository...');
    try {
      await initGit(targetDir);
      await createInitialCommit(targetDir);
      spinner.succeed('Git repository initialized');
    } catch (error) {
      spinner.warn('Git initialization failed (optional)');
    }
  }

  // Install dependencies
  if (!options.skipInstall) {
    spinner.start('Installing Node.js dependencies...');
    try {
      await installDependencies(targetDir, 'npm');
      spinner.succeed('Node.js dependencies installed');
    } catch (error) {
      spinner.warn('Failed to install dependencies');
      console.log(chalk.yellow('  Run "npm install" manually'));
    }

    spinner.start('Installing Python dependencies...');
    try {
      await installDependencies(targetDir, 'pip');
      spinner.succeed('Python dependencies installed');
    } catch (error) {
      spinner.warn('Failed to install Python dependencies');
      console.log(chalk.yellow('  Run "pip install -r requirements.txt" manually'));
    }
  }

  // Success message
  console.log();
  console.log(chalk.green.bold('✅ Service created successfully!'));
  console.log();
  console.log(chalk.bold('Next steps:'));
  console.log();
  console.log(chalk.cyan(`  cd ${serviceName}`));
  console.log(chalk.cyan('  code .'));
  console.log();
  console.log(chalk.bold('Implement your service:'));
  console.log(chalk.gray('  1. Open lambda_handler.py'));
  console.log(chalk.gray('  2. Replace the process_file() function with your logic'));
  console.log(chalk.gray('  3. Add any dependencies to requirements.txt'));
  console.log(chalk.gray('  4. Test locally: pytest tests/'));
  console.log();
  console.log(chalk.bold('Deploy to AWS:'));
  console.log(chalk.gray('  npm run deploy:dev'));
  console.log();
  console.log(chalk.bold('Documentation:'));
  console.log(chalk.gray('  README.md - Service documentation'));
  console.log(chalk.gray('  .github/workflows/README.md - CI/CD guide'));
  console.log();
}

main().catch((error) => {
  console.error(chalk.red('Fatal error:'), error);
  process.exit(1);
});
```

### Step 5: Interactive Prompts

**`src/prompts.js`**:

```javascript
const validateNpmPackageName = require('validate-npm-package-name');

function validateServiceName(name) {
  if (!name) {
    return 'Service name is required';
  }

  if (!/^[a-z0-9-]+$/.test(name)) {
    return 'Service name must be lowercase with hyphens (e.g., pdf-processor)';
  }

  const npmValidation = validateNpmPackageName(name);
  if (!npmValidation.validForNewPackages) {
    return `Invalid service name: ${npmValidation.errors?.[0] || 'must be valid npm package'}`;
  }

  return true;
}

const prompts = [
  {
    type: 'input',
    name: 'serviceId',
    message: 'Service ID (unique identifier):',
    default: (answers) => `${answers.serviceName || 'service'}-v1`,
    validate: (input) => (input ? true : 'Service ID is required'),
  },
  {
    type: 'input',
    name: 'description',
    message: 'Service description:',
    default: 'A VeloFlow Lambda service',
  },
  {
    type: 'list',
    name: 'serviceType',
    message: 'Service type:',
    choices: [
      { name: 'PDF Processor', value: 'pdf_processor' },
      { name: 'Excel Processor', value: 'excel_processor' },
      { name: 'Financial Analyzer', value: 'financial_analyzer' },
      { name: 'Data Formatter', value: 'formatter' },
      { name: 'Document Analyzer', value: 'document_analyzer' },
      { name: 'Custom', value: 'custom' },
    ],
  },
  {
    type: 'input',
    name: 'customServiceType',
    message: 'Enter custom service type:',
    when: (answers) => answers.serviceType === 'custom',
    validate: (input) => (input ? true : 'Service type is required'),
  },
  {
    type: 'list',
    name: 'inputFormat',
    message: 'Primary input format:',
    choices: ['PDF', 'Excel (XLSX)', 'CSV', 'JSON', 'Image', 'Text', 'Any'],
  },
  {
    type: 'list',
    name: 'outputFormat',
    message: 'Primary output format:',
    choices: ['Excel (XLSX)', 'JSON', 'PDF', 'CSV', 'Text', 'Any'],
  },
  {
    type: 'confirm',
    name: 'useAI',
    message: 'Does this service use AI/ML (e.g., Claude, OpenAI)?',
    default: false,
  },
  {
    type: 'list',
    name: 'aiProvider',
    message: 'Which AI provider?',
    choices: ['Anthropic (Claude)', 'OpenAI', 'AWS Bedrock', 'Other'],
    when: (answers) => answers.useAI,
  },
  {
    type: 'number',
    name: 'memorySize',
    message: 'Lambda memory size (MB):',
    default: 3008,
    validate: (input) => {
      if (input < 128 || input > 10240) {
        return 'Memory must be between 128 and 10240 MB';
      }
      return true;
    },
  },
  {
    type: 'number',
    name: 'timeout',
    message: 'Lambda timeout (seconds):',
    default: 900,
    validate: (input) => {
      if (input < 1 || input > 900) {
        return 'Timeout must be between 1 and 900 seconds';
      }
      return true;
    },
  },
  {
    type: 'confirm',
    name: 'enableRegistry',
    message: 'Register with VeloFlow service registry?',
    default: true,
  },
  {
    type: 'confirm',
    name: 'enableGithubActions',
    message: 'Set up GitHub Actions CI/CD?',
    default: true,
  },
];

module.exports = { prompts, validateServiceName };
```

### Step 6: Template Processing

**`src/template.js`**:

```javascript
const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

const FILE_REPLACEMENTS = {
  // Files to process for placeholder replacement
  'lambda_handler.py': true,
  'serverless.yml': true,
  'template.yaml': true,
  'package.json': true,
  'deploy_lambda.sh': true,
  '.env.sample': true,
  'README.md': true,
  'scripts/update_service_registry.py': true,
};

async function processTemplate(targetDir, config) {
  // Generate replacements map
  const replacements = generateReplacements(config);

  // Process each file
  for (const [file, shouldProcess] of Object.entries(FILE_REPLACEMENTS)) {
    if (shouldProcess) {
      const filePath = path.join(targetDir, file);
      if (await fs.pathExists(filePath)) {
        await replaceInFile(filePath, replacements);
      }
    }
  }

  // Remove GitHub Actions if disabled
  if (!config.enableGithubActions) {
    await fs.remove(path.join(targetDir, '.github'));
  }

  // Add AI dependencies if needed
  if (config.useAI) {
    await addAIDependencies(targetDir, config.aiProvider);
  }

  // Update serverless.yml memory and timeout
  await updateServerlessConfig(targetDir, {
    memorySize: config.memorySize,
    timeout: config.timeout,
  });
}

function generateReplacements(config) {
  const serviceType = config.customServiceType || config.serviceType;

  return {
    'service-template': config.serviceName,
    'service-template-v1': config.serviceId,
    'SERVICE_ID = "service-template-v1"': `SERVICE_ID = "${config.serviceId}"`,
    'VeloFlow Service Template': config.description,
    'Template service': config.description,
    'SERVICE_NAME = "service-template"': `SERVICE_NAME = "${config.serviceName}"`,
    'SERVICE_TYPE = "template"': `SERVICE_TYPE = "${serviceType}"`,
    'SERVICE_DISPLAY_NAME = "VeloFlow Service Template"': `SERVICE_DISPLAY_NAME = "${config.description}"`,
    '"supported_formats": ["any"]': `"supported_formats": ["${config.inputFormat.toLowerCase()}"]`,
    '"output_format": "any"': `"output_format": "${config.outputFormat.toLowerCase()}"`,
  };
}

async function replaceInFile(filePath, replacements) {
  let content = await fs.readFile(filePath, 'utf-8');

  for (const [search, replace] of Object.entries(replacements)) {
    content = content.replace(new RegExp(escapeRegex(search), 'g'), replace);
  }

  await fs.writeFile(filePath, content, 'utf-8');
}

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function addAIDependencies(targetDir, provider) {
  const requirementsPath = path.join(targetDir, 'requirements.txt');
  let content = await fs.readFile(requirementsPath, 'utf-8');

  const dependencies = {
    'Anthropic (Claude)': 'anthropic>=0.18.0',
    'OpenAI': 'openai>=1.0.0',
    'AWS Bedrock': 'boto3>=1.34.0  # Bedrock is included',
  };

  const dependency = dependencies[provider];
  if (dependency && !content.includes(dependency)) {
    content += `\n# AI Provider\n${dependency}\n`;
    await fs.writeFile(requirementsPath, content, 'utf-8');
  }
}

async function updateServerlessConfig(targetDir, { memorySize, timeout }) {
  const serverlessPath = path.join(targetDir, 'serverless.yml');
  let content = await fs.readFile(serverlessPath, 'utf-8');

  content = content.replace(/memorySize:\s*\d+/, `memorySize: ${memorySize}`);
  content = content.replace(/timeout:\s*\d+/, `timeout: ${timeout}`);

  await fs.writeFile(serverlessPath, content, 'utf-8');
}

module.exports = { processTemplate };
```

### Step 7: Git Operations

**`src/git.js`**:

```javascript
const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

async function initGit(targetDir) {
  await execAsync('git init', { cwd: targetDir });
}

async function createInitialCommit(targetDir) {
  await execAsync('git add .', { cwd: targetDir });
  await execAsync(
    'git commit -m "Initial commit: VeloFlow service scaffolded"',
    { cwd: targetDir }
  );
}

module.exports = { initGit, createInitialCommit };
```

### Step 8: Utility Functions

**`src/utils.js`**:

```javascript
const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

async function installDependencies(targetDir, type) {
  if (type === 'npm') {
    await execAsync('npm install', { cwd: targetDir });
  } else if (type === 'pip') {
    await execAsync('pip install -r requirements.txt', { cwd: targetDir });
  }
}

module.exports = { installDependencies };
```

## Publishing to npm

### Step 1: Test Locally

```bash
# In create-veloflow-service directory
npm link

# Test it
cd /tmp
npx create-veloflow-service test-service
```

### Step 2: Publish to npm

```bash
# Login to npm
npm login

# Publish (first time)
npm publish --access public

# Update version and publish
npm version patch
npm publish
```

## Usage Examples

Once published, users can:

```bash
# Interactive mode
npx create-veloflow-service

# With service name
npx create-veloflow-service my-pdf-processor

# With custom template
npx create-veloflow-service my-service --template github:myorg/custom-template

# Skip dependency installation
npx create-veloflow-service my-service --skip-install

# Skip git initialization
npx create-veloflow-service my-service --skip-git
```

## Alternative: GitHub Template Repository

For a simpler approach without npm:

1. Mark `service-template` as a GitHub template repository
2. Users click "Use this template" on GitHub
3. Clone their new repository
4. Run a setup script: `./setup.sh my-service-name`

**`setup.sh`**:
```bash
#!/bin/bash
# Simple setup script for manual template use

SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
  read -p "Service name: " SERVICE_NAME
fi

# Replace placeholders
find . -type f -not -path "*/\.git/*" -exec sed -i '' "s/service-template/$SERVICE_NAME/g" {} +

echo "✅ Service customized: $SERVICE_NAME"
```

## Recommendation

I recommend implementing the **Node.js CLI approach** because:

1. **Professional UX**: Matches industry standards (create-react-app, etc.)
2. **Cross-platform**: Works on Windows, Mac, Linux
3. **Interactive**: Guides users through configuration
4. **Automated**: Handles git, dependencies, file replacements
5. **Discoverable**: Easy to find and use via npx

Would you like me to create the initial `create-veloflow-service` package structure?
