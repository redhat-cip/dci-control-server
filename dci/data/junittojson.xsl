<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" indent="yes"/>

  <xsl:template match="/testsuite">
  {
      "name": "<xsl:value-of select="@name" />",
      "total": "<xsl:value-of select="@tests" />",
      "failures": "<xsl:value-of select="@failures" />",
      "errors": "<xsl:value-of select="@errors" />",
      "skips": "<xsl:value-of select="@skips" />",
      "time": "<xsl:value-of select="@time" />",
      "properties": [
        <xsl:for-each select="properties">
          <xsl:for-each select="property">
            {
              "name": "<xsl:value-of select="@name" />",
              "value": "<xsl:value-of select="@value" />"
            }<xsl:choose> <xsl:when test="position() != last()">,</xsl:when> </xsl:choose>
          </xsl:for-each>
        </xsl:for-each>
      ],
      "testscases": [
        <xsl:for-each select="testcase">
        {
          "name": "<xsl:value-of select="@name" />",
          "classname": "<xsl:value-of select="@classname" />",
          "file": "<xsl:value-of select="@file" />",
          "time": "<xsl:value-of select="@time" />",
          "result": <xsl:if test="not(*)"> {} </xsl:if>
            <xsl:if test="*">
              <xsl:apply-templates select="passed" />
              <xsl:apply-templates select="skipped" />
              <xsl:apply-templates select="failure" />
              <xsl:apply-templates select="error" />
            </xsl:if>
        }<xsl:choose> <xsl:when test="position() != last()">,</xsl:when> </xsl:choose>
        </xsl:for-each>
      ]
  }
  </xsl:template>

  <xsl:template match="passed">
    {
      "action": "passed",
      "message": "<xsl:value-of select="@message" />",
      "type": "<xsl:value-of select="@type" />",
      "value": "<xsl:value-of select="." />"
    }
  </xsl:template>

  <xsl:template match="error">
    {
      "action": "error",
      "message": "<xsl:value-of select="@message" />",
      "type": "<xsl:value-of select="@type" />",
      "value": "<xsl:value-of select="." />"
    }
  </xsl:template>

  <xsl:template match="failure">
    {
      "action": "failure",
      "message": "<xsl:value-of select="@message" />",
      "type": "<xsl:value-of select="@type" />",
      "value": "<xsl:value-of select="." />"
    }
  </xsl:template>

  <xsl:template match="skipped">
    {
      "action": "skipped",
      "message": "<xsl:value-of select="@message" />",
      "type": "<xsl:value-of select="@type" />",
      "value": "<xsl:value-of select="." />"
    }
  </xsl:template>

</xsl:stylesheet>
