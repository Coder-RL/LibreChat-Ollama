const express = require('express');
const router = express.Router();
const { setHeaders } = require('~/server/middleware');
const ollamaController = require('~/server/controllers/ollama/ChatController');

/**
 * @route POST /
 * @desc Chat with Ollama using the enhanced context injection
 * @access Public
 * @param {express.Request} req - The request object, containing the request data.
 * @param {express.Response} res - The response object, used to send back a response.
 * @returns {void}
 */
router.post('/', setHeaders, ollamaController);

module.exports = router;
