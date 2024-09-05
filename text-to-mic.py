"""
Scorchsoft Text to Mic
Copyright (C) 2024 Scorchsoft Ltd.

This program is free software: you can redistribute it and/or modify it under the terms of the 
GNU Lesser General Public License as published by the Free Software Foundation, either version 3 
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program. 
If not, see <https://www.gnu.org/licenses/>.

The names "Scorchsoft" and "Scorchsoft Ltd." and the associated logos are trademarks of Scorchsoft Ltd. 
You may use these names solely for the purpose of providing attribution, as required by the LGPL licence, 
and not in any way that implies an endorsement or affiliation with Scorchsoft Ltd. without explicit written permission.

Additional terms apply as described in the LICENSE.md file.

DISCLAIMER: This software is provided "as-is," and any use of this software is at your own risk.
For more information, see the LICENSE.md file included with this project.
"""

from utils.text_to_mic import TextToMic

if __name__ == "__main__":
    app = TextToMic()
    app.mainloop()