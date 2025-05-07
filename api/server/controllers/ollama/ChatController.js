const { spawn } = require('child_process');
const path = require('path');
const { logger } = require('~/config');

/**
 * Controller for handling Ollama chat requests with enhanced context injection
 *
 * @param {import('express').Request} req - The Express request object
 * @param {import('express').Response} res - The Express response object
 */
const ollamaChatController = async (req, res) => {
  try {
    logger.info('[OllamaChatController] Received request');

    const { prompt, session_id, project_id, role, model, temperature, max_tokens } = req.body;

    // Validate required parameters
    if (!prompt) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter: prompt'
      });
    }

    // Validate parameter types
    if (temperature && typeof temperature !== 'number') {
      return res.status(400).json({
        success: false,
        error: 'Invalid parameter type: temperature must be a number'
      });
    }

    if (max_tokens && typeof max_tokens !== 'number') {
      return res.status(400).json({
        success: false,
        error: 'Invalid parameter type: max_tokens must be a number'
      });
    }

    // Sanitize inputs
    const sanitizedPrompt = prompt.toString().trim();
    const sanitizedSessionId = (session_id || 'default-session').toString().trim();
    const sanitizedProjectId = (project_id || 'default-project').toString().trim();
    const sanitizedRole = (role || 'default').toString().trim();

    // Prepare parameters for the Python script
    const scriptPath = path.join(process.cwd(), 'app', 'inference_api.py');
    const args = [
      scriptPath,
      '--prompt', sanitizedPrompt,
      '--session_id', sanitizedSessionId,
      '--project_id', sanitizedProjectId,
      '--role', sanitizedRole,
    ];

    if (model) args.push('--model', model.toString().trim());
    if (temperature) args.push('--temperature', temperature.toString());
    if (max_tokens) args.push('--max_tokens', max_tokens.toString());

    logger.debug(`[OllamaChatController] Executing Python script: ${scriptPath}`);
    logger.debug(`[OllamaChatController] Args: ${args.join(' ')}`);

    // Execute the Python script with a timeout
    const pythonProcess = spawn('python3', args);

    // Set a timeout to kill the process if it takes too long
    const processTimeout = setTimeout(() => {
      logger.error('[OllamaChatController] Python process timed out, killing process');
      pythonProcess.kill();
      return res.status(504).json({
        success: false,
        error: 'Request timed out',
        details: 'The inference process took too long to complete'
      });
    }, 60000); // 60 seconds timeout

    let responseData = '';
    let errorData = '';

    // Collect data from stdout
    pythonProcess.stdout.on('data', (data) => {
      responseData += data.toString();
    });

    // Collect data from stderr
    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      logger.error(`[OllamaChatController] Python error: ${data.toString()}`);
    });

    // Handle process completion
    pythonProcess.on('close', (code) => {
      // Clear the timeout
      clearTimeout(processTimeout);

      if (code !== 0) {
        logger.error(`[OllamaChatController] Python process exited with code ${code}`);
        logger.error(`[OllamaChatController] Error: ${errorData}`);
        return res.status(500).json({
          success: false,
          error: 'Error processing request',
          details: errorData
        });
      }

      try {
        // Parse the JSON response from the Python script
        const result = JSON.parse(responseData);
        logger.info(`[OllamaChatController] Successfully processed request`);
        return res.json(result);
      } catch (parseError) {
        logger.error(`[OllamaChatController] Error parsing Python response: ${parseError.message}`);
        return res.status(500).json({
          success: false,
          error: 'Error parsing response',
          details: responseData
        });
      }
    });
  } catch (error) {
    logger.error(`[OllamaChatController] Error: ${error.message}`);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = ollamaChatController;
