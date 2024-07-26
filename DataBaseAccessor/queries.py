GET_EMAIL_INFO_QUERY = """
SELECT 
    CAST(SUM(CAST(DATEDIFF(MINUTE, '00:00:00', A.Overtime) AS DECIMAL(10, 2)) / 60.0) AS DECIMAL(10, 2)) AS TotalOvertimeHours,
    COUNT(*) AS DateCount,
    E.Email
FROM [dbo].[Attendances] A
INNER JOIN AspNetUsers E ON A.UserId = E.Id
WHERE (E.LastName + E.FirstName) = ?
  AND MONTH(A.[Date]) = MONTH(GETDATE())
  AND YEAR(A.[Date]) = YEAR(GETDATE())
GROUP BY E.Email;
"""

def get_email_info_query():
    """
    メール情報を取得するためのクエリを返す関数です。

    Returns:
        str: メール情報を取得するためのSQLクエリ
    """
    return GET_EMAIL_INFO_QUERY
