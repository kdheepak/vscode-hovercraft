import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

suite('Extension Test Suite', () => {
	vscode.window.showInformationMessage('Start all tests.');

	test('Extension should be present', () => {
		assert.ok(vscode.extensions.getExtension('kdheepak.hovercraft'));
	});

	test('Extension should activate', async function() {
		this.timeout(30000); // Increase timeout for activation
		
		const extension = vscode.extensions.getExtension('kdheepak.hovercraft');
		assert.ok(extension);
		
		if (!extension!.isActive) {
			await extension!.activate();
		}
		
		assert.ok(extension!.isActive);
	}).timeout(30000);

	test('Configuration should have expected properties', () => {
		const config = vscode.workspace.getConfiguration('hovercraft');
		
		// Test that configuration properties exist
		assert.ok(config.has('logLevel'));
		assert.ok(config.has('uvPath'));
		
		// Test default values
		assert.strictEqual(config.get('logLevel'), 'info');
		assert.strictEqual(config.get('uvPath'), '');
	});

	test('Should handle workspace without hover files gracefully', async () => {
		// Create a temporary workspace
		const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hovercraft-test-'));
		
		try {
			const workspaceUri = vscode.Uri.file(tmpDir);
			
			// This should not throw an error even without hover files
			const doc = await vscode.workspace.openTextDocument({
				content: 'console.log("test");',
				language: 'javascript'
			});
			
			const editor = await vscode.window.showTextDocument(doc);
			const position = new vscode.Position(0, 7); // Position on "log"
			
			// This should complete without error even if no hover data is available
			const hoverResult = await vscode.commands.executeCommand<vscode.Hover[]>(
				'vscode.executeHoverProvider',
				doc.uri,
				position
			);
			
			// Should return empty array or undefined, not throw
			assert.ok(Array.isArray(hoverResult) || hoverResult === undefined);
			
		} finally {
			// Clean up
			fs.rmSync(tmpDir, { recursive: true, force: true });
		}
	});
});