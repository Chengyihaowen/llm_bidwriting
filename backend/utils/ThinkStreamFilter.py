class ThinkStreamFilter:
      def __init__(self):
          self.in_think = False
          self.buffer = ''

      def feed(self, chunk: str) -> str:
          if not chunk:
              return ''

          self.buffer += chunk
          output = []

          while self.buffer:
              if self.in_think:
                  end = self.buffer.find('</think>')
                  if end == -1:
                      if len(self.buffer) > 32:
                          self.buffer = self.buffer[-32:]
                      return ''.join(output)
                  self.buffer = self.buffer[end + len('</think>'):]
                  self.in_think = False
              else:
                  start = self.buffer.find('<think>')
                  if start == -1:
                      if len(self.buffer) <= 16:
                          return ''.join(output)
                      safe_text = self.buffer[:-16]
                      self.buffer = self.buffer[-16:]
                      output.append(safe_text)
                      return ''.join(output)

                  if start > 0:
                      output.append(self.buffer[:start])

                  self.buffer = self.buffer[start + len('<think>'):]
                  self.in_think = True

          return ''.join(output)

      def flush(self) -> str:
          if self.in_think:
              return ''
          remaining = self.buffer
          self.buffer = ''
          return remaining.replace('<think>', '').replace('</think>', '')