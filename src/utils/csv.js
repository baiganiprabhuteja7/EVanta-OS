const safeCsvCell = (value) => {
  const normalized = String(value ?? '')
  const firstNonWhitespace = normalized.trimStart()[0]
  const safe = ['=', '+', '-', '@'].includes(firstNonWhitespace)
    ? `'${normalized}`
    : normalized
  return `"${safe.replaceAll('"', '""')}"`
}

export function toCsv(rows, columns) {
  const header = columns.map((column) => safeCsvCell(column.label)).join(',')
  const values = rows.map((row) =>
    columns.map((column) => safeCsvCell(column.value(row))).join(','),
  )
  return [header, ...values].join('\r\n')
}

export function downloadCsv(filename, rows, columns) {
  const content = `\uFEFF${toCsv(rows, columns)}`
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
