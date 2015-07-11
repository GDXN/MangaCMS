
Overall data-flow:

+----------+   +----------------------+   +-------------------+
| Database +-->+                      +-->+                   |
+----^-----+   |   Retreive task.     |   |  Retreive remote  |
     |         |   Filter by          |   |  resource         |
     |         |    * Priority        |   |                   |
     |         |    * Task source     |   +--------+----------+
     |         |    * Predicted       |            |           
     |         |       content-Type   |            |           
     |         |                      |            v           
     |         +----------------------+   +--------+----------+
     |         +----------------------+   |                   |
     |         |                      |   |  Process          |
     |         |  Generate update     |   |  retrieved        |
     +---------+  based on processed  +^--+  content using    |
               |  content.            |   |  plugin LUT       |
               |                      |   |                   |
               +----------------------+   +---------+---------+
                                                    ^          
                                                    |          
                                            +-------+------+   
                                            |              |   
                                            |   Build      |   
                                            |   Plugin     |   
                                            |    LUT       |   
                                            |              |   
                                            +------+-------+   
                                                   ^           
                                                   |           
                                                   |           
                                             +-----+-------+   
                                             |             |   
                                             |   Plugins   |   
                                             |             |   
                                             +-------------+   


