# PDF Download Feature

## Overview
The chatbot now includes a PDF download feature that allows users to export their chat conversations and document summaries as a professional PDF report.

## Features

### Download Buttons
- **Location**: Top-right corner of the chatbot header
- **Visibility**: Only appears when there are messages in the chat
- **Summary Button**: 
  - Icon: 📋 clipboard icon
  - Text: "Download Summary"
  - Downloads only the document summary as PDF
- **Full Report Button**:
  - Icon: 📄 document icon  
  - Text: "Download Report"
  - Downloads complete chat conversation and summary as PDF

### PDF Content

#### Summary Report PDF
The summary-only PDF includes:

1. **Header Section**
   - Title: "Document Summary Report"
   - Documents analyzed (filename list)
   - Generation timestamp

2. **Summary Section** (if available)
   - Document summaries with formatted content
   - Key findings and highlights
   - Section-wise breakdowns
   - If no summary is available, shows a message to generate one first

#### Full Report PDF
The complete report PDF includes:

1. **Header Section**
   - Title: "Document Analysis Report"
   - Documents analyzed (filename list)
   - Generation timestamp

2. **Summary Section** (if available)
   - Document summaries with formatted content
   - Key findings and highlights
   - Section-wise breakdowns

3. **Chat Conversation**
   - Complete chat history
   - User and Assistant messages
   - Timestamps for each message
   - Proper formatting and pagination

### Technical Implementation

#### Dependencies
- `jspdf`: JavaScript PDF generation library
- Installed via: `npm install jspdf`

#### Key Functions
- `downloadChatReport()`: Full report PDF generation function
- `downloadSummaryReport()`: Summary-only PDF generation function
- Both functions handle text wrapping and pagination
- Support multiple pages for long content
- Error handling with user feedback

#### Styling
- Download buttons match the existing UI design
- Summary button has different color scheme (blue tones)
- Full report button maintains original design (beige tones)
- Loading state with spinner animation for both buttons
- Disabled state when generating PDF
- Responsive design for mobile devices (buttons stack vertically)

## Usage

1. **Start a conversation** with the chatbot about your documents
2. **Generate summaries** or ask questions
3. **Choose your download option**:
   - **"Download Summary"** - Downloads only the document summary as PDF
   - **"Download Report"** - Downloads complete chat conversation and summary as PDF
4. **Wait for generation** (loading spinner will show)
5. **PDF will download** automatically with timestamped filename

## File Naming
- **Summary PDF**: `document-summary-report-YYYY-MM-DD.pdf`
- **Full Report PDF**: `document-analysis-report-YYYY-MM-DD.pdf`

## Error Handling
- If PDF generation fails, an alert will notify the user
- The download button will be re-enabled after any error
- Console errors are logged for debugging

## Browser Compatibility
- Works in all modern browsers
- Uses client-side PDF generation (no server dependency)
- No internet connection required for PDF generation

## Future Enhancements
- Custom PDF templates
- Export options (chat only, summary only, etc.)
- Email sharing functionality
- Custom branding options 