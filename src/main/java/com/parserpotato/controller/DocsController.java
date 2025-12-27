package com.parserpotato.controller;

import io.swagger.v3.oas.annotations.Hidden;
import lombok.extern.slf4j.Slf4j;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;

/**
 * Controller for serving documentation files as HTML
 */
@RestController
@RequestMapping("/docs/static")
@Slf4j
@Hidden // Hide from Swagger UI
public class DocsController {

    private static final Map<String, String> ALLOWED_DOCS = Map.of(
            "README.md", "Project Overview and Setup",
            "ARCHITECTURE.md", "System Architecture",
            "TESTING.md", "Testing Strategy",
            "EFFICIENCY_DESIGN.md", "Efficiency & Design",
            "IMPLEMENTATION_SUMMARY.md", "Implementation Summary");

    private final Parser markdownParser = Parser.builder().build();
    private final HtmlRenderer htmlRenderer = HtmlRenderer.builder().build();

    @GetMapping(value = "/{filename}", produces = MediaType.TEXT_HTML_VALUE)
    public ResponseEntity<String> getDocFile(@PathVariable String filename) {
        log.info("Serving documentation file: {}", filename);

        // Validate filename
        if (!ALLOWED_DOCS.containsKey(filename)) {
            return ResponseEntity.notFound().build();
        }

        // Read markdown file
        Path filePath = Paths.get(filename);
        if (!Files.exists(filePath)) {
            log.warn("Documentation file not found: {}", filename);
            return ResponseEntity.notFound().build();
        }

        try {
            String markdown = Files.readString(filePath);
            String htmlContent = convertMarkdownToHtml(markdown);
            String styledHtml = wrapWithStyles(htmlContent, ALLOWED_DOCS.get(filename));
            return ResponseEntity.ok(styledHtml);
        } catch (IOException e) {
            log.error("Error reading documentation file: {}", filename, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    private String convertMarkdownToHtml(String markdown) {
        var document = markdownParser.parse(markdown);
        return htmlRenderer.render(document);
    }

    private String wrapWithStyles(String htmlContent, String title) {
        return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>%s</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                            line-height: 1.6;
                            max-width: 900px;
                            margin: 0 auto;
                            padding: 40px 20px;
                            color: #24292e;
                            background-color: #ffffff;
                        }
                        h1, h2, h3, h4, h5, h6 {
                            margin-top: 24px;
                            margin-bottom: 16px;
                            font-weight: 600;
                            line-height: 1.25;
                        }
                        h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
                        h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
                        h3 { font-size: 1.25em; }
                        p { margin-top: 0; margin-bottom: 16px; }
                        a { color: #0366d6; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                        pre {
                            padding: 16px;
                            overflow: auto;
                            font-size: 85%%;
                            line-height: 1.45;
                            background-color: #f6f8fa;
                            border-radius: 6px;
                        }
                        code {
                            padding: 0.2em 0.4em;
                            margin: 0;
                            font-size: 85%%;
                            background-color: rgba(27,31,35,0.05);
                            border-radius: 3px;
                            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                        }
                        pre code {
                            display: inline;
                            padding: 0;
                            margin: 0;
                            overflow: visible;
                            line-height: inherit;
                            word-wrap: normal;
                            background-color: transparent;
                            border: 0;
                        }
                        table {
                            display: block;
                            width: 100%%;
                            overflow: auto;
                            margin-top: 0;
                            margin-bottom: 16px;
                            border-spacing: 0;
                            border-collapse: collapse;
                        }
                        table tr {
                            background-color: #fff;
                            border-top: 1px solid #c6cbd1;
                        }
                        table tr:nth-child(2n) {
                            background-color: #f6f8fa;
                        }
                        table th, table td {
                            padding: 6px 13px;
                            border: 1px solid #dfe2e5;
                        }
                        table th {
                            font-weight: 600;
                        }
                        blockquote {
                            padding: 0 1em;
                            color: #6a737d;
                            border-left: 0.25em solid #dfe2e5;
                            margin: 0;
                        }
                        ul, ol { padding-left: 2em; margin-bottom: 16px; }
                        img { max-width: 100%%; box-sizing: content-box; background-color: #fff; }
                    </style>
                </head>
                <body>
                    %s
                </body>
                </html>
                """
                .formatted(title, htmlContent);
    }

    @GetMapping("/")
    public ResponseEntity<Map<String, String>> listDocs() {
        return ResponseEntity.ok(ALLOWED_DOCS);
    }
}
