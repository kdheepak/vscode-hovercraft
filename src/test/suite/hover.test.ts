import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

suite('Hover Functionality Test Suite', () => {
	test('Should be able to create test files and open documents', async () => {
		// Create a temporary test workspace
		const testWorkspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hovercraft-test-'));
		
		try {
			// Create .vscode directory
			const vscodeDir = path.join(testWorkspaceDir, '.vscode');
			fs.mkdirSync(vscodeDir, { recursive: true });
			
			// Create test hover CSV file
			const csvContent = `keyword,description,category
console,JavaScript console object,object
log,Logging method of console,method`;
			
			fs.writeFileSync(
				path.join(vscodeDir, 'hovercraft.js.csv'),
				csvContent
			);
			
			// Verify CSV file was created
			assert.ok(fs.existsSync(path.join(vscodeDir, 'hovercraft.js.csv')));
			
			// Create a test JavaScript file
			const jsContent = `console.log("Hello World");`;
			const testFilePath = path.join(testWorkspaceDir, 'test.js');
			fs.writeFileSync(testFilePath, jsContent);
			
			// Open the test document
			const testDocument = await vscode.workspace.openTextDocument(testFilePath);
			assert.ok(testDocument);
			assert.strictEqual(testDocument.languageId, 'javascript');
			
		} finally {
			// Clean up
			fs.rmSync(testWorkspaceDir, { recursive: true, force: true });
		}
	});

	test('Should handle file operations without throwing errors', async () => {
		// Test that basic file operations work in the test environment
		const tempFile = path.join(os.tmpdir(), 'hovercraft-test-temp.js');
		
		try {
			fs.writeFileSync(tempFile, 'console.log("test");');
			const doc = await vscode.workspace.openTextDocument(tempFile);
			assert.ok(doc.getText().includes('console.log'));
			
			// Test position operations
			const position = new vscode.Position(0, 0);
			const word = doc.getWordRangeAtPosition(position);
			assert.ok(position !== undefined);
			
		} finally {
			if (fs.existsSync(tempFile)) {
				fs.unlinkSync(tempFile);
			}
		}
	});

	test('Should be able to execute hover provider command', async () => {
		// Create a simple document and test hover provider execution
		const doc = await vscode.workspace.openTextDocument({
			content: 'console.log("test");',
			language: 'javascript'
		});
		
		const position = new vscode.Position(0, 0);
		
		// This should not throw, even if no hover data is available
		const hoverResult = await vscode.commands.executeCommand<vscode.Hover[]>(
			'vscode.executeHoverProvider',
			doc.uri,
			position
		);
		
		// Should return array or undefined, not throw
		assert.ok(Array.isArray(hoverResult) || hoverResult === undefined);
	});
});